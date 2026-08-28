"""Administrative review of appeals against published community context."""

from datetime import UTC, datetime
from urllib.parse import urlparse

from flask import abort, flash, redirect, render_template, request, url_for
from flask_login import current_user

from twitclone.admin import admin_blueprint
from twitclone.admin.fact_context import FACT_CONTEXT_OUTCOMES
from twitclone.admin.routes import admin_required
from twitclone.extensions import db
from twitclone.fact_context_models import FactContextAppeal
from twitclone.models import Notification


def _utcnow():
    return datetime.now(UTC).replace(tzinfo=None)


def _valid_optional_source_url(value):
    if not value:
        return True
    try:
        parsed = urlparse(value)
    except ValueError:
        return False
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


@admin_blueprint.route("/admin/fact-context-appeals")
@admin_required
def fact_context_appeals():
    status_filter = (request.args.get("status") or "pending").strip().lower()
    if status_filter not in {"pending", "upheld", "revised", "withdrawn", "all"}:
        status_filter = "pending"
    query = FactContextAppeal.query
    if status_filter != "all":
        query = query.filter_by(status=status_filter)
    appeals = query.order_by(FactContextAppeal.created_at.asc()).all()
    return render_template(
        "admin_fact_context_appeals.html",
        appeals=appeals,
        status_filter=status_filter,
        outcomes=FACT_CONTEXT_OUTCOMES,
        pending_count=FactContextAppeal.query.filter_by(status="pending").count(),
    )


@admin_blueprint.route("/admin/fact-context-appeals/<int:appeal_id>", methods=["POST"])
@admin_required
def review_fact_context_appeal(appeal_id):
    appeal = db.get_or_404(FactContextAppeal, appeal_id)
    if appeal.status != "pending":
        flash("That appeal has already been resolved.", "info")
        return redirect(url_for("admin.fact_context_appeals"))

    action = (request.form.get("action") or "").strip().lower()
    notes = (request.form.get("resolution_notes") or "").strip() or None
    outcome = (request.form.get("resolved_outcome") or "").strip().lower() or None
    revised_context = (request.form.get("resolved_context") or "").strip() or None
    revised_source = (request.form.get("resolved_source_url") or "").strip() or None

    if action not in {"uphold", "revise", "withdraw"}:
        abort(400)
    if action == "revise":
        if outcome not in FACT_CONTEXT_OUTCOMES or not revised_context or not revised_source:
            flash("A revision requires an outcome, revised context, and supporting source URL.", "danger")
            return redirect(url_for("admin.fact_context_appeals"))
        if not _valid_optional_source_url(revised_source):
            flash("Provide a valid http or https source URL for the revision.", "danger")
            return redirect(url_for("admin.fact_context_appeals"))

    appeal.status = {"uphold": "upheld", "revise": "revised", "withdraw": "withdrawn"}[action]
    appeal.reviewed_at = _utcnow()
    appeal.reviewed_by_id = current_user.id
    appeal.resolution_notes = notes
    if action == "revise":
        appeal.resolved_outcome = outcome
        appeal.resolved_context = revised_context
        appeal.resolved_source_url = revised_source

    messages = {
        "uphold": "Your community-context appeal was reviewed; the published context was upheld.",
        "revise": "Your community-context appeal resulted in revised published context.",
        "withdraw": "Your community-context appeal resulted in the published context being withdrawn.",
    }
    db.session.add(Notification(
        user_id=appeal.appellant_id,
        message=messages[action],
        tweet_id=appeal.submission.tweet_id,
    ))
    if appeal.submission.submitter_id != appeal.appellant_id:
        db.session.add(Notification(
            user_id=appeal.submission.submitter_id,
            message=(
                "Published community context you submitted was revised after appeal review."
                if action == "revise"
                else "Published community context you submitted was withdrawn after appeal review."
                if action == "withdraw"
                else "An appeal of published community context you submitted was reviewed and the context was upheld."
            ),
            tweet_id=appeal.submission.tweet_id,
        ))
    db.session.commit()
    flash(f"Appeal resolved: {appeal.status}.", "success")
    return redirect(url_for("admin.fact_context_appeals"))


__all__ = []
