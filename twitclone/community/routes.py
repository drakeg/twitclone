"""Community standards acknowledgement and post reporting routes."""

from datetime import UTC, datetime

from flask import flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from twitclone.community import community_blueprint
from twitclone.extensions import db
from twitclone.models import Poll, PostReport, Quote, Tweet

COMMUNITY_GUIDELINES_VERSION = "2026-08-18"
REPORT_CATEGORIES = {
    "bullying": "Bullying or harassment",
    "abuse": "Rude, abusive, or demeaning behavior",
    "hate": "Hate or discrimination",
    "threats": "Threats or encouragement of violence",
    "privacy": "Privacy or personal information",
    "sexual": "Sexual harassment or inappropriate sexual content",
    "spam": "Spam, scams, or manipulation",
    "other": "Other community standards concern",
}


def _utcnow():
    return datetime.now(UTC).replace(tzinfo=None)


def _resolve_content(content_type, content_id):
    model = {"tweet": Tweet, "quote": Quote, "poll": Poll}.get(content_type)
    if model is None:
        return None
    return db.session.get(model, content_id)


@community_blueprint.before_app_request
def require_current_guidelines_acknowledgement():
    if not current_user.is_authenticated:
        return None
    if current_user.community_guidelines_version == COMMUNITY_GUIDELINES_VERSION:
        return None
    if request.endpoint in {
        "community.guidelines",
        "community.accept_guidelines",
        "logout",
        "static",
    }:
        return None
    return redirect(url_for("community.accept_guidelines"))


@community_blueprint.route("/community-guidelines")
def guidelines():
    return render_template(
        "community_guidelines.html",
        guidelines_version=COMMUNITY_GUIDELINES_VERSION,
        requires_acceptance=False,
    )


@community_blueprint.route("/community-guidelines/accept", methods=["GET", "POST"])
@login_required
def accept_guidelines():
    if current_user.community_guidelines_version == COMMUNITY_GUIDELINES_VERSION:
        return redirect(url_for("index"))

    if request.method == "POST":
        if request.form.get("accept") != "yes":
            flash("You must agree to Ripple's Community Standards to continue.", "danger")
        else:
            current_user.community_guidelines_version = COMMUNITY_GUIDELINES_VERSION
            current_user.community_guidelines_accepted_at = _utcnow()
            db.session.commit()
            flash("Thanks for helping keep Ripple welcoming and respectful.", "success")
            return redirect(url_for("index"))

    return render_template(
        "community_guidelines.html",
        guidelines_version=COMMUNITY_GUIDELINES_VERSION,
        requires_acceptance=True,
    )


@community_blueprint.route("/report/<content_type>/<int:content_id>", methods=["GET", "POST"])
@login_required
def report_content(content_type, content_id):
    content = _resolve_content(content_type, content_id)
    if content is None or getattr(content, "is_removed", False):
        flash("That content is no longer available.", "warning")
        return redirect(url_for("index"))

    author = content.user
    if author.id == current_user.id:
        flash("You cannot report your own content.", "warning")
        return redirect(url_for("index"))

    existing = PostReport.query.filter_by(
        reporter_id=current_user.id,
        content_type=content_type,
        content_id=content_id,
    ).first()
    if existing:
        flash("You have already reported this content. An admin can review it.", "info")
        return redirect(url_for("index"))

    if request.method == "POST":
        category = request.form.get("category") or ""
        details = (request.form.get("details") or "").strip() or None
        if category not in REPORT_CATEGORIES:
            flash("Choose a reason for the report.", "danger")
        else:
            db.session.add(
                PostReport(
                    reporter_id=current_user.id,
                    author_id=author.id,
                    content_type=content_type,
                    content_id=content_id,
                    category=category,
                    details=details,
                )
            )
            db.session.commit()
            flash("Report submitted. Ripple admins have been alerted for review.", "success")
            return redirect(url_for("index"))

    preview = content.content if content_type in {"tweet", "quote"} else content.question
    return render_template(
        "report_content.html",
        content=content,
        content_type=content_type,
        preview=preview,
        categories=REPORT_CATEGORIES,
    )


__all__ = ["COMMUNITY_GUIDELINES_VERSION", "REPORT_CATEGORIES"]
