"""Verification application, administration, and moderation routes."""

from collections import Counter
from datetime import UTC, datetime
from functools import wraps

from flask import abort, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from twitclone.admin import admin_blueprint
from twitclone.community.routes import REPORT_CATEGORIES
from twitclone.extensions import db
from twitclone.fact_context_models import FactContextSubmission
from twitclone.models import Notification, Poll, PostReport, Quote, Tweet, User, VerificationRequest
from twitclone.reply_models import Reply, ReplyReport


def _utcnow():
    return datetime.now(UTC).replace(tzinfo=None)


def admin_required(view):
    @wraps(view)
    @login_required
    def wrapped(*args, **kwargs):
        if not (current_user.is_admin or current_user.is_super_admin):
            abort(403)
        return view(*args, **kwargs)
    return wrapped


def _reported_content(report):
    model = {"tweet": Tweet, "quote": Quote, "poll": Poll, "reply": Reply}.get(report.content_type)
    return db.session.get(model, report.content_id) if model else None


def _content_preview(report, content):
    if content is None:
        return "Content no longer exists."
    return content.question if report.content_type == "poll" else content.content


def _all_moderation_reports():
    reports = list(PostReport.query.all()) + list(ReplyReport.query.all())
    return sorted(reports, key=lambda report: (report.created_at, report.id), reverse=True)


def _review_moderation_report(report, related_reports):
    if report.status != 'pending':
        flash('That report has already been reviewed.', 'info')
        return redirect(url_for('admin.moderation_queue'))
    action = request.form.get('action')
    notes = (request.form.get('resolution_notes') or '').strip() or None
    if action not in {'dismiss', 'remove'}:
        abort(400)
    reviewed_at = _utcnow()
    if action == 'dismiss':
        report.status = 'dismissed'
        report.reviewed_at = reviewed_at
        report.reviewed_by_id = current_user.id
        report.resolution_notes = notes
        db.session.add(Notification(user_id=report.reporter_id, message="We reviewed your report. The content will remain on Ripple because it was not found to violate the Community Standards."))
        flash('Report dismissed. No content was removed.', 'success')
    else:
        content = _reported_content(report)
        if content is not None:
            content.is_removed = True
            content.removed_at = reviewed_at
            content.removed_by_id = current_user.id
            content.removal_reason = notes or 'Removed for violating Ripple Community Standards.'
            db.session.add(Notification(user_id=report.author_id, message='A Ripple admin removed content from your account for violating the Community Standards.'))
        for related in related_reports:
            related.status = 'removed'
            related.reviewed_at = reviewed_at
            related.reviewed_by_id = current_user.id
            related.resolution_notes = notes
            db.session.add(Notification(user_id=related.reporter_id, message='We reviewed your report. The reported content was removed for violating the Ripple Community Standards.'))
        flash(f'Content removed and {len(related_reports)} related report(s) resolved.', 'success')
    db.session.commit()
    return redirect(url_for('admin.moderation_queue'))


@admin_blueprint.route('/verification/apply', methods=['GET', 'POST'])
@login_required
def apply_verification():
    active = VerificationRequest.query.filter(
        VerificationRequest.user_id == current_user.id,
        VerificationRequest.status.in_(['pending', 'approved']),
    ).order_by(VerificationRequest.submitted_at.desc()).first()
    if request.method == 'POST':
        if active:
            flash('You already have an active verification request.', 'warning')
            return redirect(url_for('admin.apply_verification'))
        verification_type = (request.form.get('verification_type') or '').strip()
        display_name = (request.form.get('display_name') or '').strip()
        official_website = (request.form.get('official_website') or '').strip() or None
        supporting_information = (request.form.get('supporting_information') or '').strip()
        if verification_type not in {'person', 'organization'}:
            flash('Choose a valid verification type.', 'danger')
        elif not display_name or not supporting_information:
            flash('Name and supporting information are required.', 'danger')
        else:
            db.session.add(VerificationRequest(user_id=current_user.id, verification_type=verification_type, display_name=display_name, official_website=official_website, supporting_information=supporting_information))
            db.session.commit()
            flash('Your verification request has been submitted for review.', 'success')
            return redirect(url_for('admin.apply_verification'))
    requests = VerificationRequest.query.filter_by(user_id=current_user.id).order_by(VerificationRequest.submitted_at.desc()).all()
    return render_template('verification_apply.html', requests=requests, active_request=active)


@admin_blueprint.route('/admin')
@admin_required
def admin_dashboard():
    pending = VerificationRequest.query.filter_by(status='pending').order_by(VerificationRequest.submitted_at.asc()).all()
    pending_reports = [report for report in _all_moderation_reports() if report.status == 'pending']
    pending_context = FactContextSubmission.query.filter_by(status='pending').order_by(FactContextSubmission.submitted_at.desc()).limit(5).all()
    moderation_rows = []
    for report in pending_reports:
        content = _reported_content(report)
        moderation_rows.append((report, _content_preview(report, content)))

    return render_template(
        'admin_dashboard.html', pending_requests=pending,
        moderation_reports=moderation_rows,
        fact_context_submissions=pending_context,
        total_users=User.query.count(),
        verified_users=User.query.filter_by(identity_verified=True).count(),
        admin_users=User.query.filter(db.or_(User.is_admin.is_(True), User.is_super_admin.is_(True))).count(),
        moderation_count=len(pending_reports),
        fact_context_count=FactContextSubmission.query.filter_by(status='pending').count(),
    )


@admin_blueprint.route('/admin/moderation')
@admin_required
def moderation_queue():
    status_filter = (request.args.get('status') or 'pending').strip().lower()
    category_filter = (request.args.get('category') or '').strip().lower()
    content_type_filter = (request.args.get('content_type') or '').strip().lower()

    if status_filter not in {'pending', 'dismissed', 'removed', 'all'}:
        status_filter = 'pending'
    if category_filter not in REPORT_CATEGORIES:
        category_filter = ''
    if content_type_filter not in {'tweet', 'quote', 'poll', 'reply'}:
        content_type_filter = ''

    all_reports = _all_moderation_reports()
    summary_counts = Counter(report.status for report in all_reports)
    content_report_counts = Counter((report.content_type, report.content_id) for report in all_reports)

    reports = [
        report for report in all_reports
        if (status_filter == 'all' or report.status == status_filter)
        and (not category_filter or report.category == category_filter)
        and (not content_type_filter or report.content_type == content_type_filter)
    ]
    rows = []
    for report in reports:
        content = _reported_content(report)
        rows.append((report, content, _content_preview(report, content), content_report_counts[(report.content_type, report.content_id)]))
    return render_template(
        'admin_moderation.html', reports=rows, categories=REPORT_CATEGORIES,
        status_filter=status_filter, category_filter=category_filter,
        content_type_filter=content_type_filter, summary_counts=summary_counts,
        total_reports=len(all_reports),
    )


@admin_blueprint.route('/admin/moderation/<int:report_id>', methods=['POST'])
@admin_required
def review_report(report_id):
    report = db.get_or_404(PostReport, report_id)
    related_reports = PostReport.query.filter_by(content_type=report.content_type, content_id=report.content_id, status='pending').all()
    return _review_moderation_report(report, related_reports)


@admin_blueprint.route('/admin/moderation/reply/<int:report_id>', methods=['POST'])
@admin_required
def review_reply_report(report_id):
    report = db.get_or_404(ReplyReport, report_id)
    related_reports = ReplyReport.query.filter_by(reply_id=report.reply_id, status='pending').all()
    return _review_moderation_report(report, related_reports)


@admin_blueprint.route('/admin/verification/<int:request_id>', methods=['GET', 'POST'])
@admin_required
def review_verification(request_id):
    verification = db.get_or_404(VerificationRequest, request_id)
    if request.method == 'POST':
        action = request.form.get('action')
        notes = (request.form.get('review_notes') or '').strip() or None
        if action not in {'approve', 'reject', 'revoke'}:
            abort(400)
        verification.reviewed_at = _utcnow(); verification.reviewed_by_id = current_user.id; verification.review_notes = notes
        user = verification.user
        if action == 'approve':
            verification.status = 'approved'; user.identity_verified = True; user.verification_type = verification.verification_type; user.verified_at = verification.reviewed_at
            flash(f'@{user.username} is now verified.', 'success')
        elif action == 'reject':
            verification.status = 'rejected'; flash('Verification request rejected.', 'success')
        else:
            verification.status = 'revoked'; user.identity_verified = False; user.verification_type = None; user.verified_at = None
            flash(f'Verification revoked for @{user.username}.', 'success')
        db.session.commit()
        return redirect(url_for('admin.admin_dashboard'))
    return render_template('admin_verification_review.html', verification=verification)


@admin_blueprint.route('/admin/users')
@admin_required
def admin_users():
    users = User.query.order_by(User.username.asc()).all()
    return render_template('admin_users.html', users=users)
