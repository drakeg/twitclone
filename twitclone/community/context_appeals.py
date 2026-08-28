"""Appeal workflow for published community fact context."""

from urllib.parse import urlparse

from flask import flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from twitclone.community import community_blueprint
from twitclone.extensions import db
from twitclone.fact_context_models import FactContextAppeal, FactContextSubmission
from twitclone.models import Notification


def _valid_optional_source_url(value):
    if not value:
        return True
    try:
        parsed = urlparse(value)
    except ValueError:
        return False
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


@community_blueprint.route("/community-context/<int:submission_id>/appeal", methods=["GET", "POST"])
@login_required
def appeal_fact_context(submission_id):
    submission = db.get_or_404(FactContextSubmission, submission_id)
    if submission.status != "approved":
        flash("Only published community context can be appealed.", "warning")
        return redirect(url_for("post_detail", tweet_id=submission.tweet_id))

    existing = FactContextAppeal.query.filter_by(
        submission_id=submission.id,
        appellant_id=current_user.id,
        status="pending",
    ).first()
    if existing:
        flash("You already have a pending appeal for this context item.", "info")
        return redirect(url_for("post_detail", tweet_id=submission.tweet_id))

    if request.method == "POST":
        reason = (request.form.get("reason") or "").strip()
        source_url = (request.form.get("source_url") or "").strip() or None
        proposed_context = (request.form.get("proposed_context") or "").strip() or None
        if not reason:
            flash("Explain why this published context should be reconsidered.", "danger")
        elif not _valid_optional_source_url(source_url):
            flash("Provide a valid http or https evidence URL.", "danger")
        else:
            appeal = FactContextAppeal(
                submission_id=submission.id,
                appellant_id=current_user.id,
                reason=reason,
                source_url=source_url,
                proposed_context=proposed_context,
            )
            db.session.add(appeal)
            db.session.add(Notification(
                user_id=current_user.id,
                message="Your appeal of published community context was submitted for review.",
                tweet_id=submission.tweet_id,
            ))
            db.session.commit()
            flash("Appeal submitted. The published context remains visible while the appeal is reviewed.", "success")
            return redirect(url_for("post_detail", tweet_id=submission.tweet_id))

    return render_template("fact_context_appeal.html", submission=submission)


__all__ = []
