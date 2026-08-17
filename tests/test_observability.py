import json
import logging

from sqlalchemy.exc import OperationalError

from twitclone.extensions import db
from twitclone.observability import JsonFormatter


def test_liveness_reports_ok_without_database_query(client, monkeypatch):
    monkeypatch.setattr(db.session, "execute", lambda *_: (_ for _ in ()).throw(AssertionError))

    response = client.get("/health/live")

    assert response.status_code == 200
    assert response.get_json() == {"status": "ok"}


def test_readiness_reports_ok_when_database_is_available(client):
    response = client.get("/health/ready")

    assert response.status_code == 200
    assert response.get_json() == {"status": "ok"}


def test_readiness_reports_unavailable_without_exposing_error(client, monkeypatch):
    def unavailable(*_args, **_kwargs):
        raise OperationalError("SELECT 1", {}, Exception("private database detail"))

    monkeypatch.setattr(db.session, "execute", unavailable)
    monkeypatch.setattr(db.session, "rollback", lambda: None)

    response = client.get("/health/ready")

    assert response.status_code == 503
    assert response.get_json() == {"status": "unavailable"}
    assert b"private database detail" not in response.data


def test_request_log_is_structured_and_propagates_correlation_id(client, caplog):
    with caplog.at_level(logging.INFO, logger="twitclone.http"):
        response = client.get("/health/live", headers={"X-Request-ID": "trace-123"})
    request_record = next(
        record
        for record in caplog.records
        if getattr(record, "event", None) == "request_completed"
    )

    assert response.headers["X-Request-ID"] == "trace-123"
    assert request_record.request_id == "trace-123"
    assert request_record.method == "GET"
    assert request_record.path == "/health/live"
    assert request_record.status == 200
    assert isinstance(request_record.duration_ms, float)


def test_unsafe_correlation_id_is_replaced(client):
    response = client.get("/health/live", headers={"X-Request-ID": "unsafe value"})

    assert response.headers["X-Request-ID"] != "unsafe value"
    assert len(response.headers["X-Request-ID"]) == 32


def test_json_formatter_includes_structured_worker_fields():
    record = logging.LogRecord(
        "twitclone.worker", logging.INFO, __file__, 1, "published", (), None
    )
    record.event = "scheduled_tweets_published"
    record.published_count = 2

    payload = json.loads(JsonFormatter().format(record))

    assert payload["level"] == "INFO"
    assert payload["event"] == "scheduled_tweets_published"
    assert payload["published_count"] == 2
