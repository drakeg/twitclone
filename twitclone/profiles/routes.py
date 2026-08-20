"""Profile and social graph routes."""

from pathlib import Path

from flask import current_app, flash, jsonify, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from twitclone.extensions import db
from twitclone.models import Notification, Quote, Retweet, Tweet, User
from twitclone.profiles import profiles_blueprint
from twitclone.timeline.media import prepare_image_upload

PROFILE_THEMES = {
    'ripple': 'Ripple Blue',
    'sunset': 'Sunset',
    'forest': 'Forest',
    'violet': 'Violet',
    'slate': 'Slate',
}


def _store_profile_banner(upload):
    error, generated_name = prepare_image_upload(upload)
    if error:
        return error, None
    banner_name = f"banner_{generated_name}"
    upload.save(Path(current_app.config['UPLOAD_FOLDER']) / banner_name)
    return None, banner_name


@login_required
def follow(username):
    user = User.query.filter_by(username=username).first()
    if user and user not in current_user.followed:
        current_user.followed.append(user)
        db.session.commit()
        notification = Notification(user_id=user.id, message=f"{current_user.username} followed you")
        db.session.add(notification)
        db.session.commit()
        return jsonify({"status": "success", "message": f"You are now following {username}."})
    if user:
        return jsonify({"status": "success", "message": f"You are now following {username}."})
    return jsonify({"status": "error", "message": "User not found."})


@login_required
def unfollow(username):
    user = User.query.filter_by(username=username).first()
    if user and user in current_user.followed:
        current_user.followed.remove(user)
        db.session.commit()
        notification = Notification(user_id=user.id, message=f"{current_user.username} unfollowed you")
        db.session.add(notification)
        db.session.commit()
        return jsonify({"status": "success", "message": f"You have unfollowed {username}."})
    if user:
        return jsonify({"status": "success", "message": f"You have unfollowed {username}."})
    return jsonify({"status": "error", "message": "User not found."})


@login_required
def profile(username):
    user = User.query.filter_by(username=username).first_or_404()
    is_following = user in current_user.followed
    premium_profile_active = user.has_entitlement('ripple_plus')
    return render_template(
        "profile.html",
        user=user,
        is_following=is_following,
        premium_profile_active=premium_profile_active,
    )


@login_required
def analytics():
    if not current_user.has_entitlement('ripple_plus'):
        flash('Personal analytics are included with Ripple+.', 'info')
        return redirect(url_for('payments.billing_home'))
    authored_tweet_ids = [row[0] for row in db.session.query(Tweet.id).filter(Tweet.user_id == current_user.id).all()]
    reposts_received = 0
    quotes_received = 0
    if authored_tweet_ids:
        reposts_received = Retweet.query.filter(Retweet.tweet_id.in_(authored_tweet_ids)).count()
        quotes_received = Quote.query.filter(Quote.tweet_id.in_(authored_tweet_ids), Quote.is_removed.is_(False)).count()
    stats = {
        'posts': Tweet.query.filter_by(user_id=current_user.id, is_removed=False).count(),
        'followers': current_user.followers.count(),
        'following': current_user.followed.count(),
        'reposts_received': reposts_received,
        'quotes_received': quotes_received,
    }
    return render_template('analytics.html', stats=stats)


@login_required
def edit_profile():
    ripple_plus = current_user.has_entitlement('ripple_plus')
    if request.method == "POST":
        current_user.username = request.form["username"]
        current_user.email = request.form["email"]
        current_user.bio = request.form["bio"]

        if ripple_plus:
            requested_theme = (request.form.get('profile_theme') or 'ripple').strip().lower()
            if requested_theme not in PROFILE_THEMES:
                flash('Choose one of the available Ripple+ profile themes.', 'danger')
                return render_template('edit_profile.html', user=current_user, ripple_plus=True, profile_themes=PROFILE_THEMES)
            current_user.profile_theme = requested_theme

            if request.form.get('remove_banner') == '1':
                current_user.profile_banner = None
            banner = request.files.get('profile_banner')
            if banner and banner.filename:
                error, banner_name = _store_profile_banner(banner)
                if error:
                    flash(error, 'danger')
                    return render_template('edit_profile.html', user=current_user, ripple_plus=True, profile_themes=PROFILE_THEMES)
                current_user.profile_banner = banner_name

        db.session.commit()
        flash("Your profile has been updated!", "success")
        return redirect(url_for("profile", username=current_user.username))
    return render_template(
        "edit_profile.html",
        user=current_user,
        ripple_plus=ripple_plus,
        profile_themes=PROFILE_THEMES,
    )


@login_required
def followers(username):
    user = User.query.filter_by(username=username).first_or_404()
    user_followers = user.followers.all()
    return render_template("followers.html", user=user, followers=user_followers)


@login_required
def following(username):
    user = User.query.filter_by(username=username).first_or_404()
    followed_users = user.followed.all()
    return render_template("following.html", user=user, following=followed_users)


@login_required
def unfollow_from_list(user_id):
    user = db.get_or_404(User, user_id)
    if user in current_user.followed:
        current_user.followed.remove(user)
        db.session.commit()
        flash(f"You have unfollowed {user.username}.", "success")
    return redirect(url_for("following", username=current_user.username))


@profiles_blueprint.record_once
def register_profile_routes(state):
    """Register routes while retaining existing endpoint names."""
    state.app.add_url_rule("/follow/<username>", endpoint="follow", view_func=follow, methods=["POST"])
    state.app.add_url_rule("/unfollow/<username>", endpoint="unfollow", view_func=unfollow, methods=["POST"])
    state.app.add_url_rule("/profile/<username>", endpoint="profile", view_func=profile)
    state.app.add_url_rule("/analytics", endpoint="analytics", view_func=analytics)
    state.app.add_url_rule("/profile/edit", endpoint="edit_profile", view_func=edit_profile, methods=["GET", "POST"])
    state.app.add_url_rule("/followers/<username>", endpoint="followers", view_func=followers)
    state.app.add_url_rule("/following/<username>", endpoint="following", view_func=following)
    state.app.add_url_rule("/unfollow_from_list/<int:user_id>", endpoint="unfollow_from_list", view_func=unfollow_from_list)
