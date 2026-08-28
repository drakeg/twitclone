"""Community standards acknowledgement, reporting, and fact-context routes."""

from collections import Counter
from datetime import UTC, datetime
from urllib.parse import urlparse

from flask import current_app, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from twitclone.community import community_blueprint
from twitclone.extensions import db
from twitclone.fact_context_models import FactContextAssessment, FactContextSubmission
from twitclone.models import Notification, Poll, PostReport, Quote, Tweet

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
FACT_CONTEXT_ASSESSMENTS = {
    "context": "Additional context",
    "disputed": "Disputed claim",
    "outdated": "Outdated information",
    "correction": "Supported correction",
    "insufficient": "Not enough evidence",
}
FACT_CONTEXT_MIN_REVIEWS = 3
FACT_CONTEXT_MIN_AGREEMENT = 2


def _utcnow():
    return datetime.now(UTC).replace(tzinfo=None)


def _resolve_content(content_type, content_id):
    model = {"tweet": Tweet, "quote": Quote, "poll": Poll}.get(content_type)
    if model is None:
        return None
    return db.session.get(model, content_id)


def _valid_source_url(value):
    try:
        parsed = urlparse(value)
    except ValueError:
        return False
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def _eligible_context_reviewer(user):
    # Import lazily so importing community routes does not initialize auth routes,
    # which depend on COMMUNITY_GUIDELINES_VERSION from this module.
    from twitclone.auth.verification import is_email_verified

    return (
        user.is_authenticated
        and is_email_verified(user)
        and user.community_guidelines_version == COMMUNITY_GUIDELINES_VERSION
    )


def _apply_context_consensus(submission):
    assessments = list(submission.community_assessments)
    if len(assessments) < FACT_CONTEXT_MIN_REVIEWS:
        return False
    counts = Counter(item.assessment for item in assessments)
    publishable = {
        key: count for key, count in counts.items()
        if key != "insufficient" and count >= FACT_CONTEXT_MIN_AGREEMENT
    }
    if not publishable:
        return False
    outcome, votes = max(publishable.items(), key=lambda item: item[1])
    if votes * 3 < len(assessments) * 2:
        return False

    submission.status = "approved"
    submission.outcome = outcome
    submission.reviewed_at = _utcnow()
    submission.reviewed_by_id = None
    submission.review_notes = (
        f"Published by community consensus: {votes} of {len(assessments)} eligible reviewers "
        f"selected {FACT_CONTEXT_ASSESSMENTS[outcome]}."
    )
    db.session.add(Notification(
        user_id=submission.submitter_id,
        message=f"Your community context was approved by reviewer consensus as {FACT_CONTEXT_ASSESSMENTS[outcome].lower()}.",
        tweet_id=submission.tweet_id,
    ))
    if submission.tweet.user_id != submission.submitter_id:
        db.session.add(Notification(
            user_id=submission.tweet.user_id,
            message="Community-reviewed context has been added to one of your posts.",
            tweet_id=submission.tweet_id,
        ))
    return True


@community_blueprint.before_app_request
def require_current_guidelines_acknowledgement():
    if current_app.config.get("TESTING") and not current_app.config.get(
        "ENFORCE_COMMUNITY_GUIDELINES_IN_TESTS", False
    ):
        return None
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


@community_blueprint.route("/post/<int:tweet_id>/context", methods=["GET", "POST"])
@login_required
def add_fact_context(tweet_id):
    tweet = db.get_or_404(Tweet, tweet_id)
    if tweet.is_removed:
        flash("That post is no longer available.", "warning")
        return redirect(url_for("index"))

    if request.method == "POST":
        claim = (request.form.get("claim") or "").strip()
        context = (request.form.get("context") or "").strip()
        source_url = (request.form.get("source_url") or "").strip()

        if not claim or not context or not source_url:
            flash("Identify the claim, explain the proposed context, and provide a source URL.", "danger")
        elif len(claim) > 300:
            flash("Keep the claim description to 300 characters or fewer.", "danger")
        elif not _valid_source_url(source_url):
            flash("Provide a valid http or https source URL.", "danger")
        else:
            db.session.add(
                FactContextSubmission(
                    tweet_id=tweet.id,
                    submitter_id=current_user.id,
                    claim=claim,
                    context=context,
                    source_url=source_url,
                )
            )
            db.session.add(
                Notification(
                    user_id=current_user.id,
                    message="Your community context submission was received for review.",
                    tweet_id=tweet.id,
                )
            )
            db.session.commit()
            flash("Context submitted. It will not appear as accepted fact context until reviewed.", "success")
            return redirect(url_for("post_detail", tweet_id=tweet.id))

    return render_template("fact_context_submit.html", tweet=tweet)


@community_blueprint.route("/community-context")
@login_required
def context_review_queue():
    if not _eligible_context_reviewer(current_user):
        flash("Community context reviewers need a verified email and current Community Standards acceptance.", "warning")
        return redirect(url_for("index"))
    submissions = FactContextSubmission.query.filter_by(status="pending").order_by(
        FactContextSubmission.submitted_at.asc()
    ).all()
    eligible = [
        item for item in submissions
        if item.submitter_id != current_user.id
        and item.tweet.user_id != current_user.id
        and not any(review.reviewer_id == current_user.id for review in item.community_assessments)
    ]
    return render_template(
        "community_fact_context_review.html",
        submissions=eligible,
        assessments=FACT_CONTEXT_ASSESSMENTS,
        min_reviews=FACT_CONTEXT_MIN_REVIEWS,
    )


@community_blueprint.route("/community-context/<int:submission_id>/assess", methods=["POST"])
@login_required
def assess_fact_context(submission_id):
    if not _eligible_context_reviewer(current_user):
        flash("You are not currently eligible to review community context.", "warning")
        return redirect(url_for("index"))
    submission = db.get_or_404(FactContextSubmission, submission_id)
    if submission.status != "pending":
        flash("That context submission is no longer awaiting review.", "info")
        return redirect(url_for("community.context_review_queue"))
    if current_user.id in {submission.submitter_id, submission.tweet.user_id}:
        flash("Submitters and post authors cannot review this context item.", "warning")
        return redirect(url_for("community.context_review_queue"))
    if FactContextAssessment.query.filter_by(
        submission_id=submission.id,
        reviewer_id=current_user.id,
    ).first():
        flash("You have already reviewed this context item.", "info")
        return redirect(url_for("community.context_review_queue"))

    assessment = (request.form.get("assessment") or "").strip().lower()
    note = (request.form.get("note") or "").strip() or None
    if assessment not in FACT_CONTEXT_ASSESSMENTS:
        flash("Choose a valid assessment.", "danger")
        return redirect(url_for("community.context_review_queue"))
    if note and len(note) > 500:
        flash("Keep reviewer notes to 500 characters or fewer.", "danger")
        return redirect(url_for("community.context_review_queue"))

    db.session.add(FactContextAssessment(
        submission_id=submission.id,
        reviewer_id=current_user.id,
        assessment=assessment,
        note=note,
    ))
    db.session.flush()
    published = _apply_context_consensus(submission)
    db.session.commit()
    flash(
        "Your independent assessment was recorded. The context reached community consensus and is now published."
        if published else
        "Your independent assessment was recorded. The item remains pending until consensus or admin review.",
        "success",
    )
    return redirect(url_for("community.context_review_queue"))


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
            db.session.add(
                Notification(
                    user_id=current_user.id,
                    message="Your report was received and is awaiting Ripple admin review.",
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


__all__ = [
    "COMMUNITY_GUIDELINES_VERSION",
    "FACT_CONTEXT_ASSESSMENTS",
    "FACT_CONTEXT_MIN_REVIEWS",
    "REPORT_CATEGORIES",
]
