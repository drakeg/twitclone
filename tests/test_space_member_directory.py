"""Sprint 36 Story 36.1 member directory privacy coverage."""

from twitclone.extensions import db
from twitclone.models import User
from twitclone.spaces.models import Space, SpaceMembership


def _login(client, user_id):
    with client.session_transaction() as session:
        session["_user_id"] = str(user_id)
        session["_fresh"] = True


def _fixture(app):
    with app.app_context():
        owner = User(
            username="directory_owner",
            email="directory-owner@example.com",
            password="hash",
            bio="Public owner bio.",
        )
        visible = User(
            username="directory_visible",
            email="directory-visible@example.com",
            password="hash",
            bio="Public visible bio.",
        )
        hidden = User(
            username="directory_hidden",
            email="directory-hidden@example.com",
            password="hash",
            bio="Public hidden bio.",
        )
        outsider = User(
            username="directory_outsider",
            email="directory-outsider@example.com",
            password="hash",
        )
        db.session.add_all([owner, visible, hidden, outsider])
        db.session.flush()
        space = Space(
            slug="directory-space",
            name="Directory Space",
            description="Directory coverage.",
            owner_id=owner.id,
        )
        db.session.add(space)
        db.session.flush()
        db.session.add_all(
            [
                SpaceMembership(
                    space_id=space.id,
                    user_id=owner.id,
                    role="owner",
                    directory_visible=False,
                ),
                SpaceMembership(
                    space_id=space.id,
                    user_id=visible.id,
                    role="member",
                    directory_visible=True,
                ),
                SpaceMembership(
                    space_id=space.id,
                    user_id=hidden.id,
                    role="member",
                    directory_visible=False,
                ),
            ]
        )
        db.session.commit()
        return {
            "slug": space.slug,
            "space_id": space.id,
            "owner": owner.id,
            "visible": visible.id,
            "hidden": hidden.id,
            "outsider": outsider.id,
        }


def test_directory_is_member_only_and_shows_only_opted_in_members(client, app):
    ids = _fixture(app)
    _login(client, ids["owner"])

    response = client.get(f"/spaces/{ids['slug']}/directory")
    assert response.status_code == 200
    assert b'data-directory-user="directory_visible"' in response.data
    assert b"Public visible bio." in response.data
    assert b'data-directory-user="directory_hidden"' not in response.data
    assert b'data-directory-user="directory_owner"' not in response.data
    assert b"directory-visible@example.com" not in response.data

    _login(client, ids["outsider"])
    assert client.get(f"/spaces/{ids['slug']}/directory").status_code == 403


def test_directory_visibility_defaults_private(client, app):
    ids = _fixture(app)
    with app.app_context():
        newcomer = User(
            username="directory_new",
            email="directory-new@example.com",
            password="hash",
        )
        db.session.add(newcomer)
        db.session.flush()
        membership = SpaceMembership(
            space_id=ids["space_id"],
            user_id=newcomer.id,
            role="member",
        )
        db.session.add(membership)
        db.session.commit()
        assert membership.directory_visible is False


def test_member_can_opt_in_and_back_out_without_operator_approval(client, app):
    ids = _fixture(app)
    _login(client, ids["hidden"])

    opt_in = client.post(
        f"/spaces/{ids['slug']}/directory-preference",
        data={"directory_visible": "yes"},
    )
    assert opt_in.status_code == 302

    directory = client.get(f"/spaces/{ids['slug']}/directory")
    assert b'data-directory-user="directory_hidden"' in directory.data

    opt_out = client.post(
        f"/spaces/{ids['slug']}/directory-preference",
        data={"directory_visible": "no"},
    )
    assert opt_out.status_code == 302
    directory = client.get(f"/spaces/{ids['slug']}/directory")
    assert b'data-directory-user="directory_hidden"' not in directory.data


def test_nonmember_cannot_change_directory_preference(client, app):
    ids = _fixture(app)
    _login(client, ids["outsider"])

    response = client.post(
        f"/spaces/{ids['slug']}/directory-preference",
        data={"directory_visible": "yes"},
    )
    assert response.status_code == 403


def test_directory_search_is_case_insensitive_and_deterministic(client, app):
    ids = _fixture(app)
    with app.app_context():
        for username in ("AlphaMember", "alphamember2"):
            user = User(
                username=username,
                email=f"{username}@example.com",
                password="hash",
            )
            db.session.add(user)
            db.session.flush()
            db.session.add(
                SpaceMembership(
                    space_id=ids["space_id"],
                    user_id=user.id,
                    role="member",
                    directory_visible=True,
                )
            )
        db.session.commit()

    _login(client, ids["visible"])
    response = client.get(
        f"/spaces/{ids['slug']}/directory?q=ALPHAMEMBER"
    )
    body = response.data

    assert response.status_code == 200
    assert body.index(b'data-directory-user="AlphaMember"') < body.index(
        b'data-directory-user="alphamember2"'
    )
    assert b'data-directory-user="directory_visible"' not in body


def test_archived_space_keeps_directory_and_privacy_preference_available(client, app):
    ids = _fixture(app)
    with app.app_context():
        space = db.session.get(Space, ids["space_id"])
        space.archived_at = space.created_at
        space.archived_by_id = ids["owner"]
        db.session.commit()

    _login(client, ids["hidden"])
    assert client.post(
        f"/spaces/{ids['slug']}/directory-preference",
        data={"directory_visible": "yes"},
    ).status_code == 302
    assert client.get(f"/spaces/{ids['slug']}/directory").status_code == 200


def test_directory_role_filter_is_opt_in_only(client, app):
    ids = _fixture(app)
    with app.app_context():
        space = db.session.get(Space, ids["space_id"])
        owner_membership = SpaceMembership.query.filter_by(
            space_id=space.id,
            user_id=ids["owner"],
        ).one()
        owner_membership.directory_visible = True
        visible_membership = SpaceMembership.query.filter_by(
            space_id=space.id,
            user_id=ids["visible"],
        ).one()
        visible_membership.role = "moderator"
        db.session.commit()

    _login(client, ids["visible"])

    moderators = client.get(
        f"/spaces/{ids['slug']}/directory?role=moderator"
    )
    assert b'data-directory-user="directory_visible"' in moderators.data
    assert b'data-directory-user="directory_owner"' not in moderators.data

    owners = client.get(f"/spaces/{ids['slug']}/directory?role=owner")
    assert b'data-directory-user="directory_owner"' in owners.data
    assert b'data-directory-user="directory_visible"' not in owners.data


def test_invalid_directory_role_filter_falls_back_to_all_visible(client, app):
    ids = _fixture(app)
    _login(client, ids["visible"])

    response = client.get(
        f"/spaces/{ids['slug']}/directory?role=administrator"
    )

    assert response.status_code == 200
    assert b'data-directory-user="directory_visible"' in response.data
    assert b"All roles" in response.data


def test_directory_pagination_links_preserve_search_and_role(client, app, monkeypatch):
    ids = _fixture(app)
    with app.app_context():
        for index in range(30):
            user = User(
                username=f"directory_page_{index:02d}",
                email=f"directory-page-{index:02d}@example.com",
                password="hash",
            )
            db.session.add(user)
            db.session.flush()
            db.session.add(
                SpaceMembership(
                    space_id=ids["space_id"],
                    user_id=user.id,
                    role="member",
                    directory_visible=True,
                )
            )
        db.session.commit()

    _login(client, ids["visible"])
    response = client.get(
        f"/spaces/{ids['slug']}/directory?q=directory_page&role=member&page=1"
    )

    assert response.status_code == 200
    assert b"page=2" in response.data
    assert b"q=directory_page" in response.data
    assert b"role=member" in response.data
    assert b"View public profile" in response.data
