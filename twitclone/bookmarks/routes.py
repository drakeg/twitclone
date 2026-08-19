"""Bookmark creation, organization, and listing routes."""

from flask import abort, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from twitclone.bookmarks import bookmarks_blueprint
from twitclone.extensions import db
from twitclone.models import Bookmark, BookmarkFolder, Tweet


def _require_ripple_plus():
    if not current_user.has_entitlement('ripple_plus'):
        flash('Bookmark folders are a Ripple+ feature.', 'info')
        return redirect(url_for('payments.billing_home'))
    return None


@login_required
def bookmark(tweet_id):
    tweet = db.get_or_404(Tweet, tweet_id)
    if tweet.is_removed:
        abort(404)
    existing = Bookmark.query.filter_by(user_id=current_user.id, tweet_id=tweet.id).first()
    if existing is None:
        db.session.add(Bookmark(user_id=current_user.id, tweet_id=tweet.id))
        db.session.commit()
    flash("Tweet has been bookmarked!", "success")
    return redirect(url_for("index"))


@login_required
def bookmarks():
    folder_id = request.args.get('folder', type=int)
    query = (
        Bookmark.query.join(Bookmark.tweet)
        .filter(Bookmark.user_id == current_user.id, Tweet.is_removed.is_(False))
    )
    selected_folder = None
    if folder_id is not None:
        selected_folder = BookmarkFolder.query.filter_by(id=folder_id, user_id=current_user.id).first_or_404()
        query = query.filter(Bookmark.folder_id == selected_folder.id)
    saved_bookmarks = query.order_by(Bookmark.timestamp.desc()).all()
    folders = BookmarkFolder.query.filter_by(user_id=current_user.id).order_by(BookmarkFolder.name.asc()).all()
    return render_template(
        "bookmarks.html",
        bookmarks=saved_bookmarks,
        folders=folders,
        selected_folder=selected_folder,
        ripple_plus=current_user.has_entitlement('ripple_plus'),
    )


@login_required
def create_folder():
    redirect_response = _require_ripple_plus()
    if redirect_response:
        return redirect_response
    name = (request.form.get('name') or '').strip()
    if not name:
        flash('Folder name is required.', 'danger')
    elif len(name) > 80:
        flash('Folder names are limited to 80 characters.', 'danger')
    elif BookmarkFolder.query.filter_by(user_id=current_user.id, name=name).first():
        flash('You already have a bookmark folder with that name.', 'warning')
    else:
        db.session.add(BookmarkFolder(user_id=current_user.id, name=name))
        db.session.commit()
        flash(f'Created bookmark folder “{name}”.', 'success')
    return redirect(url_for('bookmarks'))


@login_required
def move_bookmark(bookmark_id):
    redirect_response = _require_ripple_plus()
    if redirect_response:
        return redirect_response
    bookmark_item = Bookmark.query.filter_by(id=bookmark_id, user_id=current_user.id).first_or_404()
    raw_folder_id = request.form.get('folder_id')
    if not raw_folder_id:
        bookmark_item.folder_id = None
    else:
        try:
            folder_id = int(raw_folder_id)
        except (TypeError, ValueError):
            abort(400)
        folder = BookmarkFolder.query.filter_by(id=folder_id, user_id=current_user.id).first_or_404()
        bookmark_item.folder_id = folder.id
    db.session.commit()
    flash('Bookmark organization updated.', 'success')
    return redirect(url_for('bookmarks'))


@login_required
def delete_folder(folder_id):
    redirect_response = _require_ripple_plus()
    if redirect_response:
        return redirect_response
    folder = BookmarkFolder.query.filter_by(id=folder_id, user_id=current_user.id).first_or_404()
    Bookmark.query.filter_by(user_id=current_user.id, folder_id=folder.id).update({'folder_id': None})
    db.session.delete(folder)
    db.session.commit()
    flash('Bookmark folder deleted. Its bookmarks remain saved.', 'success')
    return redirect(url_for('bookmarks'))


@bookmarks_blueprint.record_once
def register_bookmark_routes(state):
    state.app.add_url_rule("/bookmark/<int:tweet_id>", endpoint="bookmark", view_func=bookmark, methods=["POST"])
    state.app.add_url_rule("/bookmarks", endpoint="bookmarks", view_func=bookmarks)
    state.app.add_url_rule("/bookmarks/folders", endpoint="create_bookmark_folder", view_func=create_folder, methods=["POST"])
    state.app.add_url_rule("/bookmarks/<int:bookmark_id>/folder", endpoint="move_bookmark", view_func=move_bookmark, methods=["POST"])
    state.app.add_url_rule("/bookmarks/folders/<int:folder_id>/delete", endpoint="delete_bookmark_folder", view_func=delete_folder, methods=["POST"])
