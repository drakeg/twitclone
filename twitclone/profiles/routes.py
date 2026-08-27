"""Profile and social graph routes."""

from flask import flash, jsonify, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from twitclone.analytics_tracking import record_profile_visit, snapshot_followers
from twitclone.auth.recovery import (
    generate_email_verification_token,
    send_email_verification_email,
)
from twitclone.auth.verification import mark_email_unverified
from twitclone.creator_analytics import build_creator_dashboard
from twitclone.creator_trends import build_daily_trends
from twitclone.extensions import db
from twitclone.models import Notification, Quote, Retweet, Tweet, User
from twitclone.media_storage import get_media_storage
from twitclone.profiles import profiles_blueprint
from twitclone.timeline.media import store_profile_banner

PROFILE_THEMES = {'ripple':'Ripple Blue','sunset':'Sunset','forest':'Forest','violet':'Violet','slate':'Slate'}


def _store_profile_banner(upload):
    return store_profile_banner(upload, get_media_storage())


def _send_email_change_verification(user):
    token = generate_email_verification_token(user.email, user.password)
    send_email_verification_email(
        recipient=user.email,
        username=user.username,
        verification_url=url_for('verify_email', token=token, _external=True),
    )


@login_required
def follow(username):
    user = User.query.filter_by(username=username).first()
    if user and user not in current_user.followed:
        current_user.followed.append(user); db.session.commit(); snapshot_followers(user); db.session.add(Notification(user_id=user.id, message=f"{current_user.username} followed you")); db.session.commit(); return jsonify({'status':'success','message':f'You are now following {username}.'})
    if user: return jsonify({'status':'success','message':f'You are now following {username}.'})
    return jsonify({'status':'error','message':'User not found.'})


@login_required
def unfollow(username):
    user = User.query.filter_by(username=username).first()
    if user and user in current_user.followed:
        current_user.followed.remove(user); db.session.commit(); snapshot_followers(user); db.session.add(Notification(user_id=user.id, message=f"{current_user.username} unfollowed you")); db.session.commit(); return jsonify({'status':'success','message':f'You have unfollowed {username}.'})
    if user: return jsonify({'status':'success','message':f'You have unfollowed {username}.'})
    return jsonify({'status':'error','message':'User not found.'})


@login_required
def profile(username):
    user = User.query.filter_by(username=username).first_or_404(); record_profile_visit(user); is_following = user in current_user.followed; premium_profile_active = user.has_entitlement('ripple_plus')
    return render_template('profile.html', user=user, is_following=is_following, premium_profile_active=premium_profile_active)


def _analytics_counts(user):
    tweets = Tweet.query.filter_by(user_id=user.id, is_removed=False).all(); tweet_ids = [tweet.id for tweet in tweets]
    reposts = Retweet.query.filter(Retweet.tweet_id.in_(tweet_ids)).count() if tweet_ids else 0
    quotes = Quote.query.filter(Quote.tweet_id.in_(tweet_ids), Quote.is_removed.is_(False)).count() if tweet_ids else 0
    return tweets, {'posts':len(tweets),'followers':user.followers.count(),'following':user.followed.count(),'reposts_received':reposts,'quotes_received':quotes}


@login_required
def analytics():
    if not (current_user.has_entitlement('ripple_plus') or current_user.has_entitlement('creator_pro')):
        flash('Analytics are included with Ripple+ and Creator Pro.', 'info'); return redirect(url_for('payments.billing_home'))
    _, stats = _analytics_counts(current_user)
    return render_template('analytics.html', stats=stats)


@login_required
def creator_analytics():
    if not current_user.has_entitlement('creator_pro'):
        flash('Advanced creator analytics are included with Creator Pro.', 'info'); return redirect(url_for('payments.billing_home'))
    dashboard = build_creator_dashboard(current_user, request.args.get('days'))
    dashboard['daily_trends'] = build_daily_trends(
        current_user.id, dashboard['range_start'], dashboard['range_end']
    )
    return render_template('creator_analytics.html', **dashboard)


@login_required
def edit_profile():
    ripple_plus = current_user.has_entitlement('ripple_plus')
    if request.method == 'POST':
        requested_email = request.form['email'].strip()
        email_changed = requested_email.casefold() != current_user.email.casefold()
        if email_changed and User.query.filter(
            db.func.lower(User.email) == requested_email.lower(),
            User.id != current_user.id,
        ).first():
            flash('That email address is already registered to another Ripple account.', 'danger')
            return render_template('edit_profile.html', user=current_user, ripple_plus=ripple_plus, profile_themes=PROFILE_THEMES)

        current_user.username=request.form['username']; current_user.email=requested_email; current_user.bio=request.form['bio']
        if ripple_plus:
            requested_theme=(request.form.get('profile_theme') or 'ripple').strip().lower()
            if requested_theme not in PROFILE_THEMES: flash('Choose one of the available Ripple+ profile themes.','danger'); return render_template('edit_profile.html',user=current_user,ripple_plus=True,profile_themes=PROFILE_THEMES)
            current_user.profile_theme=requested_theme
            if request.form.get('remove_banner')=='1': current_user.profile_banner=None
            banner=request.files.get('profile_banner')
            if banner and banner.filename:
                error,banner_name=_store_profile_banner(banner)
                if error: flash(error,'danger'); return render_template('edit_profile.html',user=current_user,ripple_plus=True,profile_themes=PROFILE_THEMES)
                current_user.profile_banner=banner_name
        if email_changed:
            mark_email_unverified(current_user.id)
        db.session.commit()
        if email_changed:
            _send_email_change_verification(current_user)
            flash('Your profile was updated. Please verify your new email address.', 'warning')
        else:
            flash('Your profile has been updated!','success')
        return redirect(url_for('profile',username=current_user.username))
    return render_template('edit_profile.html',user=current_user,ripple_plus=ripple_plus,profile_themes=PROFILE_THEMES)


@login_required
def followers(username):
    user=User.query.filter_by(username=username).first_or_404(); return render_template('followers.html',user=user,followers=user.followers.all())
@login_required
def following(username):
    user=User.query.filter_by(username=username).first_or_404(); return render_template('following.html',user=user,following=user.followed.all())
@login_required
def unfollow_from_list(user_id):
    user=db.get_or_404(User,user_id)
    if user in current_user.followed: current_user.followed.remove(user); db.session.commit(); snapshot_followers(user); flash(f'You have unfollowed {user.username}.','success')
    return redirect(url_for('following',username=current_user.username))


@profiles_blueprint.record_once
def register_profile_routes(state):
    state.app.add_url_rule('/follow/<username>',endpoint='follow',view_func=follow,methods=['POST']); state.app.add_url_rule('/unfollow/<username>',endpoint='unfollow',view_func=unfollow,methods=['POST']); state.app.add_url_rule('/profile/<username>',endpoint='profile',view_func=profile); state.app.add_url_rule('/analytics',endpoint='analytics',view_func=analytics); state.app.add_url_rule('/creator/analytics',endpoint='creator_analytics',view_func=creator_analytics); state.app.add_url_rule('/profile/edit',endpoint='edit_profile',view_func=edit_profile,methods=['GET','POST']); state.app.add_url_rule('/followers/<username>',endpoint='followers',view_func=followers); state.app.add_url_rule('/following/<username>',endpoint='following',view_func=following); state.app.add_url_rule('/unfollow_from_list/<int:user_id>',endpoint='unfollow_from_list',view_func=unfollow_from_list)
