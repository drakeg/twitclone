"""Verification application and admin review routes."""

from datetime import UTC, datetime
from functools import wraps

from flask import abort, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from twitclone.admin import admin_blueprint
from twitclone.extensions import db
from twitclone.models import User, VerificationRequest


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
            verification = VerificationRequest(
                user_id=current_user.id,
                verification_type=verification_type,
                display_name=display_name,
                official_website=official_website,
                supporting_information=supporting_information,
            )
            db.session.add(verification)
            db.session.commit()
            flash('Your verification request has been submitted for review.', 'success')
            return redirect(url_for('admin.apply_verification'))

    requests = VerificationRequest.query.filter_by(user_id=current_user.id).order_by(
        VerificationRequest.submitted_at.desc()
    ).all()
    return render_template('verification_apply.html', requests=requests, active_request=active)


@admin_blueprint.route('/admin')
@admin_required
def admin_dashboard():
    pending = VerificationRequest.query.filter_by(status='pending').order_by(
        VerificationRequest.submitted_at.asc()
    ).all()
    return render_template('admin_dashboard.html', pending_requests=pending)


@admin_blueprint.route('/admin/verification/<int:request_id>', methods=['GET', 'POST'])
@admin_required
def review_verification(request_id):
    verification = db.get_or_404(VerificationRequest, request_id)
    if request.method == 'POST':
        action = request.form.get('action')
        notes = (request.form.get('review_notes') or '').strip() or None
        if action not in {'approve', 'reject', 'revoke'}:
            abort(400)

        verification.reviewed_at = _utcnow()
        verification.reviewed_by_id = current_user.id
        verification.review_notes = notes
        user = verification.user
        if action == 'approve':
            verification.status = 'approved'
            user.identity_verified = True
            user.verification_type = verification.verification_type
            user.verified_at = verification.reviewed_at
            flash(f'@{user.username} is now verified.', 'success')
        elif action == 'reject':
            verification.status = 'rejected'
            flash('Verification request rejected.', 'success')
        else:
            verification.status = 'revoked'
            user.identity_verified = False
            user.verification_type = None
            user.verified_at = None
            flash(f'Verification revoked for @{user.username}.', 'success')
        db.session.commit()
        return redirect(url_for('admin.admin_dashboard'))

    return render_template('admin_verification_review.html', verification=verification)


@admin_blueprint.route('/admin/users')
@admin_required
def admin_users():
    users = User.query.order_by(User.username.asc()).all()
    return render_template('admin_users.html', users=users)
