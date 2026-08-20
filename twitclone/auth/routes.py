"""Authentication routes."""

from datetime import UTC, datetime

from flask import flash, redirect, render_template, request, url_for
from flask_login import login_required, login_user, logout_user

from twitclone.auth import auth_blueprint
from sqlalchemy.exc import IntegrityError

from twitclone.auth.recovery import (
    generate_reset_token,
    reset_token_matches_password,
    send_recovery_email,
    verify_reset_token,
)
from twitclone.community.routes import COMMUNITY_GUIDELINES_VERSION
from twitclone.extensions import bcrypt, db
from twitclone.models import User


def register():
    if request.method == "POST":
        username = request.form["username"]
        email = request.form["email"]
        password = request.form["password"]
        if request.form.get("community_standards") != "yes":
            flash("You must agree to the Ripple Community Standards to create an account.", "danger")
            return render_template("register.html")
        if User.query.filter(db.or_(User.username == username, User.email == email)).first():
            flash("That username or email is already registered.", "danger")
            return render_template("register.html")
        hashed_password = bcrypt.generate_password_hash(password).decode("utf-8")
        user = User(
            username=username,
            email=email,
            password=hashed_password,
            community_guidelines_version=COMMUNITY_GUIDELINES_VERSION,
            community_guidelines_accepted_at=datetime.now(UTC).replace(tzinfo=None),
        )
        db.session.add(user)
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            flash("That username or email is already registered.", "danger")
            return render_template("register.html")
        flash("Your account has been created!", "success")
        return redirect(url_for("login"))
    return render_template("register.html")


def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]
        user = User.query.filter_by(email=email).first()
        if user and bcrypt.check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for("index"))
        flash("Login Unsuccessful. Please check email and password", "danger")
    return render_template("login.html")


def forgot_account():
    if request.method == "POST":
        email = (request.form.get("email") or "").strip().lower()
        user = User.query.filter(db.func.lower(User.email) == email).first() if email else None
        if user:
            token = generate_reset_token(user.email, user.password)
            reset_url = url_for("reset_password", token=token, _external=True)
            send_recovery_email(
                recipient=user.email,
                username=user.username,
                reset_url=reset_url,
            )
        flash(
            "If that email belongs to a Ripple account, recovery instructions have been sent.",
            "info",
        )
        return redirect(url_for("login"))
    return render_template("forgot_account.html")


def reset_password(token):
    payload = verify_reset_token(token)
    if payload is None:
        flash("That password reset link is invalid or has expired.", "danger")
        return redirect(url_for("forgot_account"))

    user = User.query.filter_by(email=payload["email"]).first()
    if user is None or not reset_token_matches_password(payload, user.password):
        flash("That password reset link is invalid or has expired.", "danger")
        return redirect(url_for("forgot_account"))

    if request.method == "POST":
        password = request.form.get("password") or ""
        confirmation = request.form.get("password_confirm") or ""
        if len(password) < 8:
            flash("Password must be at least 8 characters.", "danger")
        elif password != confirmation:
            flash("Passwords do not match.", "danger")
        else:
            user.password = bcrypt.generate_password_hash(password).decode("utf-8")
            db.session.commit()
            flash("Your password has been reset. You can log in now.", "success")
            return redirect(url_for("login"))

    return render_template("reset_password.html", username=user.username)


@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))


@auth_blueprint.record_once
def register_authentication_routes(state):
    """Register routes while retaining the legacy endpoint names."""
    state.app.add_url_rule(
        "/register", endpoint="register", view_func=register, methods=["GET", "POST"]
    )
    state.app.add_url_rule(
        "/login", endpoint="login", view_func=login, methods=["GET", "POST"]
    )
    state.app.add_url_rule(
        "/forgot-account",
        endpoint="forgot_account",
        view_func=forgot_account,
        methods=["GET", "POST"],
    )
    state.app.add_url_rule(
        "/reset-password/<token>",
        endpoint="reset_password",
        view_func=reset_password,
        methods=["GET", "POST"],
    )
    state.app.add_url_rule("/logout", endpoint="logout", view_func=logout)
