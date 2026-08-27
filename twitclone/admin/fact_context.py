"""Admin review workflow for evidence-backed community fact context."""

from datetime import UTC, datetime

from flask import abort, flash, redirect, render_template, request, url_for
from flask_login import current_user

from twitclone.admin import admin_blueprint
from twitclone.admin.routes import admin_required
from twitclone.extensions import db
from twitclone.fact_context_models import FactContextSubmission
from twitclone.models import Notification

FACT_CONTEXT_OUTCOMES = {
    "context": "Additional context",
    "disputed": "Disputed claim",
    "outdated": "Outdated information",
    "correction": "Supported correction",
}


def _utcnow():
    return datetime.now(UTC).replace(tzinfo=None)


@admin_blueprint.route("/admin/fact-context")
@admin_required
def fact_context_queue():
    status_filter = (request.args.get("status") or "pending").strip().lower()
    if status_filter not in {"pending", "approved", "rejected", "all"}:
        status_filter = "pending"

    query = FactContextSubmission.query
    if status_filter != "all":
        query = query.filter_by(status=status_filter)
    submissions = query.order_by(FactContextSubmission.submitted_at.desc()).all()
    return render_template(
        "admin_fact_context.html",
        submissions=submissions,
        status_filter=status_filter,
        outcomes=FACT_CONTEXT_OUTCOMES,
        pending_count=FactContextSubmission.query.filter_by(status="pending").count(),
    )


@admin_blueprint.route("/admin/fact-context/<int:submission_id>", methods=["POST"])
@admin_required
def review_fact_context(submission_id):
    submission = db.get_or_404(FactContextSubmission, submission_id)
    if submission.status != "pending":
        flash("That context submission has already been reviewed.", "info")
        return redirect(url_for("admin.fact_context_queue"))

    action = request.form.get("action")
    outcome = (request.form.get("outcome") or "").strip().lower()
    notes = (request.form.get("review_notes") or "").strip() or None
    if action not in {"approve", "reject"}:
        abort(400)
    if action == "approve" and outcome not in FACT_CONTEXT_OUTCOMES:
        flash("Choose an accepted context outcome before approving.", "danger")
        return redirect(url_for("admin.fact_context_queue"))

    submission.status = "approved" if action == "approve" else "rejected"
    submission.outcome = outcome if action == "approve" else None
    submission.reviewed_at = _utcnow()
    submission.reviewed_by_id = current_user.id
    submission.review_notes = notes

    if action == "approve":
        db.session.add(Notification(
            user_id=submission.submitter_id,
            message=f"Your community context submission was approved as {FACT_CONTEXT_OUTCOMES[outcome].lower()}.",
            tweet_id=submission.tweet_id,
        ))
        if submission.tweet.user_id != submission.submitter_id:
            db.session.add(Notification(
                user_id=submission.tweet.user_id,
                message="Reviewed community context has been added to one of your posts.",
                tweet_id=submission.tweet_id,
            ))
        flash("Community context approved and attached to the post.", "success")
    else:
        db.session.add(Notification(
            user_id=submission.submitter_id,
            message="Your community context submission was reviewed but was not approved for publication.",
            tweet_id=submission.tweet_id,
        ))
        flash("Community context submission rejected.", "success")

    db.session.commit()
    return redirect(url_for("admin.fact_context_queue"))


__all__ = ["FACT_CONTEXT_OUTCOMES"]
