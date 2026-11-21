"""Space operator member roster and Sprint 32 CSV export coverage."""

from twitclone.extensions import db
from twitclone.models import User
from twitclone.spaces.models import Space, SpaceMembership, SpaceMembershipAction


def _login(client, user_id):
    with client.session_transaction() as session:
        session["_user_id"] = str(user_id)
        session["_fresh"] = True


def _fixture(app, member_count=30):
    with app.app_context():
        owner = User(username="roster_owner", email="owner-roster@example.com", password="hash")
        moderator = User(username="roster_moderator", email="moderator-roster@example.com", password="hash")
        regular = User(username="roster_regular", email="regular-roster@example.com", password="hash")
        db.session.add_all([owner, moderator, regular])
        db.session.flush()

        space = Space(
            slug="roster-space",
            name="Roster Space",
            description="Operator member roster coverage.",
            owner_id=owner.id,
        )
        db.session.add(space)
        db.session.flush()
        db.session.add_all([
            SpaceMembership(space_id=space.id, user_id=owner.id, role="owner"),
            SpaceMembership(space_id=space.id, user_id=moderator.id, role="moderator"),
            SpaceMembership(space_id=space.id, user_id=regular.id, role="member"),
        ])

        extra_ids = []
        for index in range(member_count):
            user = User(
                username=f"member_{index:02d}",
                email=f"private-{index:02d}@example.com",
                password="hash",
            )
            db.session.add(user)
            db.session.flush()
            db.session.add(
                SpaceMembership(space_id=space.id, user_id=user.id, role="member")
            )
            extra_ids.append(user.id)

        db.session.commit()
        return {
            "slug": space.slug,
            "owner": owner.id,
            "moderator": moderator.id,
            "regular": regular.id,
            "extra_ids": extra_ids,
        }


def test_owner_and_moderator_can_view_member_roster(client, app):
    ids = _fixture(app, member_count=2)

    _login(client, ids["owner"])
    owner_page = client.get(f"/spaces/{ids['slug']}/members")
    assert owner_page.status_code == 200
    assert b"Member roster" in owner_page.data
    assert b"roster_owner" in owner_page.data
    assert b"roster_moderator" in owner_page.data

    _login(client, ids["moderator"])
    moderator_page = client.get(f"/spaces/{ids['slug']}/members")
    assert moderator_page.status_code == 200
    assert b"Member roster" in moderator_page.data


def test_regular_member_and_anonymous_user_cannot_view_roster(client, app):
    ids = _fixture(app, member_count=1)

    _login(client, ids["regular"])
    assert client.get(f"/spaces/{ids['slug']}/members").status_code == 403

    with client.session_transaction() as session:
        session.clear()
    anonymous = client.get(f"/spaces/{ids['slug']}/members")
    assert anonymous.status_code == 302
    assert "/login" in anonymous.headers["Location"]


def test_roster_search_is_case_insensitive_and_does_not_expose_email(client, app):
    ids = _fixture(app, member_count=3)
    _login(client, ids["owner"])

    response = client.get(f"/spaces/{ids['slug']}/members?q=MEMBER_01")
    assert response.status_code == 200
    assert b'data-member-roster-row="member_01"' in response.data
    assert b'data-member-roster-row="member_00"' not in response.data
    assert b"private-01@example.com" not in response.data
    assert b'data-member-result-count="1"' in response.data


def test_roster_role_filter_limits_results(client, app):
    ids = _fixture(app, member_count=2)
    _login(client, ids["owner"])

    response = client.get(f"/spaces/{ids['slug']}/members?role=moderator")
    assert response.status_code == 200
    assert b'data-member-roster-row="roster_moderator"' in response.data
    assert b'data-member-roster-row="roster_owner"' not in response.data
    assert b'data-member-roster-row="roster_regular"' not in response.data
    assert b'data-member-result-count="1"' in response.data


def test_roster_uses_bounded_deterministic_pagination(client, app):
    ids = _fixture(app, member_count=30)
    _login(client, ids["owner"])

    first = client.get(f"/spaces/{ids['slug']}/members")
    assert first.status_code == 200
    assert b"Page 1 of 2" in first.data
    assert b'data-member-roster-row="member_00"' in first.data
    assert b'data-member-roster-row="member_29"' not in first.data

    second = client.get(f"/spaces/{ids['slug']}/members?page=2")
    assert second.status_code == 200
    assert b"Page 2 of 2" in second.data
    assert b'data-member-roster-row="member_29"' in second.data

    bounded = client.get(f"/spaces/{ids['slug']}/members?page=999")
    assert bounded.status_code == 200
    assert b"Page 2 of 2" in bounded.data


def test_owner_can_change_role_from_roster_and_return_to_filters(client, app):
    ids = _fixture(app, member_count=2)
    target_id = ids["extra_ids"][1]
    _login(client, ids["owner"])

    response = client.post(
        f"/spaces/{ids['slug']}/members/{target_id}/role",
        data={
            "role": "moderator",
            "return_to": "roster",
            "roster_q": "member_01",
            "roster_role": "member",
            "roster_page": "2",
        },
    )
    assert response.status_code == 302
    assert "/members" in response.headers["Location"]
    assert "q=member_01" in response.headers["Location"]
    assert "role=member" in response.headers["Location"]
    assert "page=2" in response.headers["Location"]

    with app.app_context():
        membership = SpaceMembership.query.filter_by(user_id=target_id).one()
        assert membership.role == "moderator"
        action = SpaceMembershipAction.query.filter_by(
            affected_user_id=target_id,
            action_type="role_changed",
        ).one()
        assert action.previous_role == "member"
        assert action.new_role == "moderator"


def test_owner_can_remove_member_from_roster_and_return_to_filters(client, app):
    ids = _fixture(app, member_count=2)
    target_id = ids["extra_ids"][0]
    _login(client, ids["owner"])

    response = client.post(
        f"/spaces/{ids['slug']}/members/{target_id}/remove",
        data={
            "confirm": "remove",
            "return_to": "roster",
            "roster_q": "member",
            "roster_role": "member",
            "roster_page": "1",
        },
    )
    assert response.status_code == 302
    assert "/members" in response.headers["Location"]
    assert "q=member" in response.headers["Location"]
    assert "role=member" in response.headers["Location"]

    with app.app_context():
        assert SpaceMembership.query.filter_by(user_id=target_id).first() is None
        action = SpaceMembershipAction.query.filter_by(
            affected_user_id=target_id,
            action_type="member_removed",
        ).one()
        assert action.previous_role == "member"
        assert action.new_role is None


def test_moderator_roster_has_no_owner_action_controls(client, app):
    ids = _fixture(app, member_count=1)
    _login(client, ids["moderator"])

    response = client.get(f"/spaces/{ids['slug']}/members")
    assert response.status_code == 200
    assert b"Owner actions" not in response.data
    assert b"Save role" not in response.data
    assert b"Remove member" not in response.data


def test_owner_row_has_no_role_or_removal_shortcut(client, app):
    ids = _fixture(app, member_count=1)
    _login(client, ids["owner"])

    response = client.get(f"/spaces/{ids['slug']}/members?role=owner")
    assert response.status_code == 200
    assert b"Transfer ownership from the Space page." in response.data
    assert b"Save role" not in response.data
    assert b"Remove member" not in response.data


def test_detail_page_role_action_keeps_existing_detail_redirect(client, app):
    ids = _fixture(app, member_count=1)
    target_id = ids["extra_ids"][0]
    _login(client, ids["owner"])

    response = client.post(
        f"/spaces/{ids['slug']}/members/{target_id}/role",
        data={"role": "moderator"},
    )
    assert response.status_code == 302
    assert response.headers["Location"].endswith(f"/spaces/{ids['slug']}")


def test_invalid_role_filter_falls_back_to_all_roles(client, app):
    ids = _fixture(app, member_count=1)
    _login(client, ids["owner"])

    response = client.get(f"/spaces/{ids['slug']}/members?role=administrator")
    assert response.status_code == 200
    assert b'data-member-roster-row="roster_owner"' in response.data
    assert b'data-member-roster-row="roster_moderator"' in response.data
    assert b'data-member-roster-row="roster_regular"' in response.data


def test_empty_search_has_clear_zero_result_state(client, app):
    ids = _fixture(app, member_count=1)
    _login(client, ids["owner"])

    response = client.get(f"/spaces/{ids['slug']}/members?q=no-such-member")
    assert response.status_code == 200
    assert b'data-member-result-count="0"' in response.data
    assert b"No members match these filters." in response.data


def test_nonpositive_page_is_bounded_to_first_page(client, app):
    ids = _fixture(app, member_count=30)
    _login(client, ids["owner"])

    response = client.get(f"/spaces/{ids['slug']}/members?page=-10")
    assert response.status_code == 200
    assert b"Page 1 of 2" in response.data
    assert b'data-member-roster-row="member_00"' in response.data


def test_pagination_links_preserve_search_and_role_filters(client, app):
    ids = _fixture(app, member_count=30)
    _login(client, ids["owner"])

    response = client.get(f"/spaces/{ids['slug']}/members?q=member&role=member")
    assert response.status_code == 200
    assert b"q=member" in response.data
    assert b"role=member" in response.data
    assert b"page=2" in response.data


def test_archived_space_keeps_operator_roster_readable(client, app):
    ids = _fixture(app, member_count=1)
    with app.app_context():
        space = Space.query.filter_by(slug=ids["slug"]).one()
        space.archived_at = space.created_at
        space.archived_by_id = ids["owner"]
        db.session.commit()

    _login(client, ids["owner"])
    response = client.get(f"/spaces/{ids['slug']}/members")
    assert response.status_code == 200
    assert b"Member roster" in response.data


def test_owner_and_moderator_can_export_filtered_roster_csv(client, app):
    ids = _fixture(app, member_count=3)

    _login(client, ids["owner"])
    owner_export = client.get(
        f"/spaces/{ids['slug']}/members/export.csv?q=MEMBER&role=member"
    )
    assert owner_export.status_code == 200
    assert owner_export.mimetype == "text/csv"
    assert owner_export.headers["Content-Disposition"] == (
        'attachment; filename="roster-space-members.csv"'
    )
    lines = owner_export.data.decode().splitlines()
    assert lines[0] == "username,space_role,joined_at"
    assert [line.split(",", 1)[0] for line in lines[1:]] == [
        "member_00",
        "member_01",
        "member_02",
    ]

    _login(client, ids["moderator"])
    moderator_export = client.get(
        f"/spaces/{ids['slug']}/members/export.csv?role=moderator"
    )
    assert moderator_export.status_code == 200
    assert b"roster_moderator,moderator," in moderator_export.data
    assert b"roster_owner" not in moderator_export.data


def test_roster_export_is_operator_only(client, app):
    ids = _fixture(app, member_count=1)

    _login(client, ids["regular"])
    assert client.get(
        f"/spaces/{ids['slug']}/members/export.csv"
    ).status_code == 403

    with client.session_transaction() as session:
        session.clear()
    anonymous = client.get(f"/spaces/{ids['slug']}/members/export.csv")
    assert anonymous.status_code == 302
    assert "/login" in anonymous.headers["Location"]


def test_roster_export_excludes_private_account_data(client, app):
    ids = _fixture(app, member_count=1)
    _login(client, ids["owner"])

    response = client.get(f"/spaces/{ids['slug']}/members/export.csv")
    body = response.data.decode()

    assert response.status_code == 200
    assert "email" not in body.splitlines()[0].lower()
    assert "private-00@example.com" not in body
    assert "owner-roster@example.com" not in body
    assert "password" not in body.lower()


def test_roster_export_matches_case_insensitive_search_and_role_filters(client, app):
    ids = _fixture(app, member_count=3)
    _login(client, ids["owner"])

    response = client.get(
        f"/spaces/{ids['slug']}/members/export.csv?q=MEMBER_01&role=member"
    )
    body = response.data.decode()

    assert response.status_code == 200
    assert "member_01,member," in body
    assert "member_00" not in body
    assert "member_02" not in body


def test_roster_page_export_link_preserves_filters_and_documents_cap(client, app):
    ids = _fixture(app, member_count=2)
    _login(client, ids["owner"])

    response = client.get(
        f"/spaces/{ids['slug']}/members?q=member&role=member"
    )

    assert response.status_code == 200
    assert b"Export CSV" in response.data
    assert b"export.csv?q=member&amp;role=member" in response.data
    assert b"capped at 5000 rows" in response.data


def test_roster_export_enforces_bounded_safe_maximum(client, app, monkeypatch):
    ids = _fixture(app, member_count=3)
    _login(client, ids["owner"])
    monkeypatch.setattr("twitclone.spaces.routes._MEMBER_EXPORT_MAX_ROWS", 2)

    response = client.get(
        f"/spaces/{ids['slug']}/members/export.csv?q=member_&role=member"
    )

    assert response.status_code == 413
    assert b"Membership export is limited to 2 rows" in response.data


def test_archived_space_roster_remains_exportable(client, app):
    ids = _fixture(app, member_count=1)
    with app.app_context():
        space = Space.query.filter_by(slug=ids["slug"]).one()
        space.archived_at = space.created_at
        space.archived_by_id = ids["owner"]
        db.session.commit()

    _login(client, ids["owner"])
    response = client.get(f"/spaces/{ids['slug']}/members/export.csv")

    assert response.status_code == 200
    assert b"roster_owner,owner," in response.data
