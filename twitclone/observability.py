"""Health endpoints and structured application logging."""

from __future__ import annotations

import json
import logging
import re
import time
from datetime import UTC, datetime
from uuid import uuid4

from flask import Blueprint, Flask, Response, g, jsonify, request
from sqlalchemy import text

from twitclone.extensions import db


health_blueprint = Blueprint("health", __name__)
log = logging.getLogger("twitclone.http")
REQUEST_ID_PATTERN = re.compile(r"[A-Za-z0-9._:-]{1,128}\Z")


class JsonFormatter(logging.Formatter):
    """Render stable, one-line JSON records for container log collection."""

    def format(self, record: logging.LogRecord) -> str:
        event = {
            "timestamp": datetime.fromtimestamp(record.created, UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        for field in (
            "event",
            "request_id",
            "method",
            "path",
            "status",
            "duration_ms",
            "published_count",
        ):
            if hasattr(record, field):
                event[field] = getattr(record, field)
        if record.exc_info:
            event["exception"] = self.formatException(record.exc_info)
        return json.dumps(event, separators=(",", ":"), ensure_ascii=True)


def configure_logging() -> None:
    """Configure the TwitClone logger hierarchy exactly once."""

    package_logger = logging.getLogger("twitclone")
    if not any(getattr(handler, "twitclone_json", False) for handler in package_logger.handlers):
        handler = logging.StreamHandler()
        handler.setFormatter(JsonFormatter())
        handler.twitclone_json = True
        package_logger.addHandler(handler)
    package_logger.setLevel(logging.INFO)
    package_logger.propagate = False


@health_blueprint.get("/health/live")
def live() -> Response:
    """Report whether the web process can serve requests."""

    return jsonify(status="ok")


@health_blueprint.get("/health/ready")
def ready() -> tuple[Response, int] | Response:
    """Report whether the application can query its configured database."""

    try:
        db.session.execute(text("SELECT 1"))
    except Exception:
        try:
            db.session.rollback()
        except Exception:
            pass
        return jsonify(status="unavailable"), 503
    return jsonify(status="ok")


def configure_observability(app: Flask) -> None:
    """Attach health routes and request logging to an application once."""

    configure_logging()
    if health_blueprint.name not in app.blueprints:
        app.register_blueprint(health_blueprint)
    if app.extensions.get("twitclone_observability"):
        return

    @app.before_request
    def start_request_observation() -> None:
        supplied_id = request.headers.get("X-Request-ID", "").strip()
        g.request_id = (
            supplied_id if REQUEST_ID_PATTERN.fullmatch(supplied_id) else uuid4().hex
        )
        g.request_started_at = time.perf_counter()

    @app.after_request
    def log_request(response: Response) -> Response:
        duration_ms = round((time.perf_counter() - g.request_started_at) * 1000, 2)
        response.headers["X-Request-ID"] = g.request_id
        log.info(
            "request_completed",
            extra={
                "event": "request_completed",
                "request_id": g.request_id,
                "method": request.method,
                "path": request.path,
                "status": response.status_code,
                "duration_ms": duration_ms,
            },
        )
        return response

    app.extensions["twitclone_observability"] = True


__all__ = ["JsonFormatter", "configure_logging", "configure_observability", "health_blueprint"]
