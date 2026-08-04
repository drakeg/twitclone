"""Authentication routes."""

from flask import flash, redirect, render_template, request, url_for
from flask_login import login_required, login_user, logout_user

from twitclone.auth import auth_blueprint
from twitclone.extensions import bcrypt, db
from twitclone.models import User


def register():
    if request.method == "POST":
        username = request.form["username"]
        email = request.form["email"]
        password = request.form["password"]
        hashed_password = bcrypt.generate_password_hash(password).decode("utf-8")
        user = User(username=username, email=email, password=hashed_password)
        db.session.add(user)
        db.session.commit()
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
    state.app.add_url_rule("/logout", endpoint="logout", view_func=logout)
