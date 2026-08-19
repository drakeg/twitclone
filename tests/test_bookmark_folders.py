"""Regression coverage for Ripple+ bookmark folders."""

from twitclone.billing import grant_entitlement
from twitclone.extensions import db
from twitclone.models import Bookmark, BookmarkFolder, Tweet, User


def _login(client, user_id):
    with client.session_transaction() as session:
        session['_user_id'] = str(user_id)
        session['_fresh'] = True


def _user(app, username, *, plus=False):
    with app.app_context():
        user = User(username=username, email=f'{username}@example.com', password='hash')
        db.session.add(user)
        db.session.flush()
        if plus:
            grant_entitlement(user, 'ripple_plus', source='admin')
        db.session.commit()
        return user.id


def _bookmark(app, user_id, content='Saved post'):
    with app.app_context():
        tweet = Tweet(user_id=user_id, content=content)
        db.session.add(tweet)
        db.session.flush()
        bookmark = Bookmark(user_id=user_id, tweet_id=tweet.id)
        db.session.add(bookmark)
        db.session.commit()
        return bookmark.id


def test_free_user_keeps_bookmarks_but_cannot_create_folder(client, app):
    user_id = _user(app, 'freeuser')
    _bookmark(app, user_id)
    _login(client, user_id)

    page = client.get('/bookmarks')
    assert page.status_code == 200
    assert b'Saved post' in page.data
    assert b'Organize with Ripple+' in page.data

    response = client.post('/bookmarks/folders', data={'name': 'Research'})
    assert response.status_code == 302
    assert '/billing' in response.headers['Location']
    with app.app_context():
        assert BookmarkFolder.query.filter_by(user_id=user_id).count() == 0


def test_ripple_plus_user_can_create_folder_and_file_bookmark(client, app):
    user_id = _user(app, 'plususer', plus=True)
    bookmark_id = _bookmark(app, user_id)
    _login(client, user_id)

    response = client.post('/bookmarks/folders', data={'name': 'Research'})
    assert response.status_code == 302
    with app.app_context():
        folder = BookmarkFolder.query.filter_by(user_id=user_id, name='Research').one()
        folder_id = folder.id

    response = client.post(f'/bookmarks/{bookmark_id}/folder', data={'folder_id': str(folder_id)})
    assert response.status_code == 302
    with app.app_context():
        assert db.session.get(Bookmark, bookmark_id).folder_id == folder_id

    page = client.get(f'/bookmarks?folder={folder_id}')
    assert page.status_code == 200
    assert b'Research' in page.data
    assert b'Saved post' in page.data


def test_user_cannot_use_another_users_folder(client, app):
    user_id = _user(app, 'ownerplus', plus=True)
    other_id = _user(app, 'otherplus', plus=True)
    bookmark_id = _bookmark(app, user_id)
    with app.app_context():
        foreign_folder = BookmarkFolder(user_id=other_id, name='Private')
        db.session.add(foreign_folder)
        db.session.commit()
        foreign_folder_id = foreign_folder.id
    _login(client, user_id)

    response = client.post(f'/bookmarks/{bookmark_id}/folder', data={'folder_id': str(foreign_folder_id)})
    assert response.status_code == 404
    with app.app_context():
        assert db.session.get(Bookmark, bookmark_id).folder_id is None


def test_deleting_folder_preserves_bookmarks_as_unfiled(client, app):
    user_id = _user(app, 'cleanupplus', plus=True)
    bookmark_id = _bookmark(app, user_id)
    with app.app_context():
        folder = BookmarkFolder(user_id=user_id, name='Later')
        db.session.add(folder)
        db.session.flush()
        db.session.get(Bookmark, bookmark_id).folder_id = folder.id
        db.session.commit()
        folder_id = folder.id
    _login(client, user_id)

    response = client.post(f'/bookmarks/folders/{folder_id}/delete')
    assert response.status_code == 302
    with app.app_context():
        assert db.session.get(BookmarkFolder, folder_id) is None
        bookmark = db.session.get(Bookmark, bookmark_id)
        assert bookmark is not None
        assert bookmark.folder_id is None
