"""Profile and social graph routes."""

from flask import flash, jsonify, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from twitclone.extensions import db
from twitclone.models import Notification, User
from twitclone.profiles import profiles_blueprint


@login_required
def follow(username):
    user = User.query.filter_by(username=username).first()
    if user:
        current_user.followed.append(user)
        db.session.commit()
        notification = Notification(
            user_id=user.id, message=f"{current_user.username} followed you"
        )
        db.session.add(notification)
        db.session.commit()
        return jsonify(
            {"status": "success", "message": f"You are now following {username}."}
        )
    return jsonify({"status": "error", "message": "User not found."})


@login_required
def unfollow(username):
    user = User.query.filter_by(username=username).first()
    if user:
        current_user.followed.remove(user)
        db.session.commit()
        notification = Notification(
            user_id=user.id, message=f"{current_user.username} unfollowed you"
        )
        db.session.add(notification)
        db.session.commit()
        return jsonify(
            {"status": "success", "message": f"You have unfollowed {username}."}
        )
    return jsonify({"status": "error", "message": "User not found."})


@login_required
def profile(username):
    user = User.query.filter_by(username=username).first_or_404()
    is_following = user in current_user.followed
    return render_template("profile.html", user=user, is_following=is_following)


@login_required
def edit_profile():
    if request.method == "POST":
        current_user.username = request.form["username"]
        current_user.email = request.form["email"]
        current_user.bio = request.form["bio"]
        db.session.commit()
        flash("Your profile has been updated!", "success")
        return redirect(url_for("profile", username=current_user.username))
    return render_template("edit_profile.html", user=current_user)


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
    user = User.query.get_or_404(user_id)
    if user in current_user.followed:
        current_user.followed.remove(user)
        db.session.commit()
        flash(f"You have unfollowed {user.username}.", "success")
    return redirect(url_for("following", username=current_user.username))


@profiles_blueprint.record_once
def register_profile_routes(state):
    """Register routes while retaining existing endpoint names."""
    state.app.add_url_rule(
        "/follow/<username>", endpoint="follow", view_func=follow, methods=["POST"]
    )
    state.app.add_url_rule(
        "/unfollow/<username>",
        endpoint="unfollow",
        view_func=unfollow,
        methods=["POST"],
    )
    state.app.add_url_rule(
        "/profile/<username>", endpoint="profile", view_func=profile
    )
    state.app.add_url_rule(
        "/profile/edit",
        endpoint="edit_profile",
        view_func=edit_profile,
        methods=["GET", "POST"],
    )
    state.app.add_url_rule(
        "/followers/<username>", endpoint="followers", view_func=followers
    )
    state.app.add_url_rule(
        "/following/<username>", endpoint="following", view_func=following
    )
    state.app.add_url_rule(
        "/unfollow_from_list/<int:user_id>",
        endpoint="unfollow_from_list",
        view_func=unfollow_from_list,
    )
