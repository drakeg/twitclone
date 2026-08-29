"""Routes for persistent community/topic spaces."""

import re

from flask import abort, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from twitclone.extensions import db
from twitclone.models import Tweet
from twitclone.spaces import spaces_blueprint
from twitclone.spaces.models import Space, SpaceMembership, SpacePost
from twitclone.timeline.validation import validate_post_content

_SLUG_RE = re.compile(r"[^a-z0-9]+")


def _slugify(value):
    slug = _SLUG_RE.sub("-", (value or "").strip().casefold()).strip("-")
    return slug[:80]


def _membership(space):
    if not current_user.is_authenticated:
        return None
    return SpaceMembership.query.filter_by(space_id=space.id, user_id=current_user.id).first()


def _visible_space_posts(space):
    return (
        SpacePost.query.join(SpacePost.tweet)
        .filter(SpacePost.space_id == space.id, Tweet.is_removed.is_(False))
        .order_by(Tweet.timestamp.desc(), SpacePost.id.desc())
        .all()
    )


@spaces_blueprint.get("/")
def index():
    spaces = Space.query.order_by(Space.name.asc(), Space.id.asc()).all()
    memberships = set()
    if current_user.is_authenticated:
        memberships = {
            row.space_id
            for row in SpaceMembership.query.filter_by(user_id=current_user.id).all()
        }
    return render_template("spaces/index.html", spaces=spaces, memberships=memberships)


@spaces_blueprint.route("/create", methods=["GET", "POST"])
@login_required
def create():
    if request.method == "POST":
        name = (request.form.get("name") or "").strip()
        description = (request.form.get("description") or "").strip()
        slug = _slugify(request.form.get("slug") or name)
        if not name or len(name) > 120:
            flash("Space name must be between 1 and 120 characters.", "danger")
            return render_template("spaces/create.html"), 400
        if not description or len(description) > 500:
            flash("Space description must be between 1 and 500 characters.", "danger")
            return render_template("spaces/create.html"), 400
        if not slug:
            flash("Choose a name that produces a usable space URL.", "danger")
            return render_template("spaces/create.html"), 400
        if Space.query.filter_by(slug=slug).first() is not None:
            flash("That space URL is already in use.", "danger")
            return render_template("spaces/create.html"), 400
        space = Space(name=name, slug=slug, description=description, owner_id=current_user.id)
        db.session.add(space)
        db.session.flush()
        db.session.add(SpaceMembership(space_id=space.id, user_id=current_user.id, role="owner"))
        db.session.commit()
        flash("Space created.", "success")
        return redirect(url_for("spaces.detail", slug=space.slug))
    return render_template("spaces/create.html")


@spaces_blueprint.get("/<slug>")
def detail(slug):
    space = Space.query.filter_by(slug=slug).first_or_404()
    membership = _membership(space)
    member_count = SpaceMembership.query.filter_by(space_id=space.id).count()
    return render_template(
        "spaces/detail.html",
        space=space,
        membership=membership,
        member_count=member_count,
        space_posts=_visible_space_posts(space),
    )


@spaces_blueprint.post("/<slug>/posts")
@login_required
def publish_post(slug):
    space = Space.query.filter_by(slug=slug).first_or_404()
    membership = _membership(space)
    if membership is None:
        abort(403)
    content = request.form.get("content")
    validation_error = validate_post_content(content, post_type="Space post")
    if validation_error:
        flash(validation_error, "danger")
        return redirect(url_for("spaces.detail", slug=space.slug))
    tweet = Tweet(content=content, user_id=current_user.id)
    db.session.add(tweet)
    db.session.flush()
    db.session.add(SpacePost(space_id=space.id, tweet_id=tweet.id))
    db.session.commit()
    flash(f"Posted in {space.name}.", "success")
    return redirect(url_for("spaces.detail", slug=space.slug))


@spaces_blueprint.post("/<slug>/join")
@login_required
def join(slug):
    space = Space.query.filter_by(slug=slug).first_or_404()
    existing = _membership(space)
    if existing is None:
        db.session.add(SpaceMembership(space_id=space.id, user_id=current_user.id, role="member"))
        db.session.commit()
        flash(f"You joined {space.name}.", "success")
    return redirect(url_for("spaces.detail", slug=space.slug))


@spaces_blueprint.post("/<slug>/leave")
@login_required
def leave(slug):
    space = Space.query.filter_by(slug=slug).first_or_404()
    membership = _membership(space)
    if membership is None:
        return redirect(url_for("spaces.detail", slug=space.slug))
    if membership.role == "owner" or space.owner_id == current_user.id:
        abort(400, description="A space owner cannot leave their space without transferring ownership.")
    db.session.delete(membership)
    db.session.commit()
    flash(f"You left {space.name}.", "success")
    return redirect(url_for("spaces.detail", slug=space.slug))
