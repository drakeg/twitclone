"""Focused tests for the polls Blueprint."""

from flask import url_for
import pytest
from sqlalchemy.exc import IntegrityError

from twitclone.extensions import db
from twitclone.models import Poll, PollOption, PollVote, User
from twitclone.polls.routes import create_poll, vote_poll


def create_logged_in_user(client, app):
    with app.app_context():
        user = User(username="alice", email="alice@example.com", password="hash")
        db.session.add(user)
        db.session.commit()
        user_id = user.id
    with client.session_transaction() as session:
        session["_user_id"] = str(user_id)
        session["_fresh"] = True
    return user_id


def test_polls_blueprint_owns_existing_routes(app):
    assert "polls" in app.blueprints
    assert app.view_functions["create_poll"] is create_poll
    assert app.view_functions["vote_poll"] is vote_poll

    with app.test_request_context():
        assert url_for("create_poll") == "/create_poll"
        assert url_for("vote_poll", poll_id=1) == "/vote_poll/1"


def test_poll_creation_preserves_models_and_redirect(client, app):
    user_id = create_logged_in_user(client, app)

    response = client.post(
        "/create_poll",
        data={
            "question": "Which option?",
            "options-0-option_text": "First",
            "options-1-option_text": "Second",
            "duration_days": "1",
            "duration_hours": "2",
            "duration_minutes": "3",
        },
    )

    assert response.status_code == 302
    assert response.headers["Location"] == "/"
    with app.app_context():
        poll = Poll.query.one()
        assert poll.question == "Which option?"
        assert poll.user_id == user_id
        assert (poll.duration_days, poll.duration_hours, poll.duration_minutes) == (
            1,
            2,
            3,
        )
        assert [option.option_text for option in poll.options] == ["First", "Second"]


def test_vote_creation_and_duplicate_handling_are_preserved(client, app):
    user_id = create_logged_in_user(client, app)
    with app.app_context():
        poll = Poll(
            question="Choose",
            duration_days=1,
            duration_hours=0,
            duration_minutes=0,
            user_id=user_id,
        )
        db.session.add(poll)
        db.session.commit()
        option = PollOption(option_text="Only", poll_id=poll.id)
        db.session.add(option)
        db.session.commit()
        poll_id = poll.id
        option_id = option.id

    first_response = client.post(
        f"/vote_poll/{poll_id}", data={"option_id": str(option_id)}
    )
    duplicate_response = client.post(
        f"/vote_poll/{poll_id}", data={"option_id": str(option_id)}
    )

    assert first_response.status_code == 302
    assert first_response.headers["Location"] == "/"
    assert duplicate_response.status_code == 302
    assert duplicate_response.headers["Location"] == "/"
    with app.app_context():
        assert PollVote.query.filter_by(poll_id=poll_id, user_id=user_id).count() == 1
        assert db.session.get(PollOption, option_id).votes == 1


def test_missing_option_and_anonymous_access_preserve_redirects(client, app):
    assert client.get("/create_poll").headers["Location"].startswith("/login?")
    assert client.post("/vote_poll/1").headers["Location"].startswith("/login?")

    create_logged_in_user(client, app)
    response = client.post("/vote_poll/999", data={})
    assert response.status_code == 302
    assert response.headers["Location"] == "/"


def test_database_rejects_second_vote_for_same_user_and_poll(client, app):
    user_id = create_logged_in_user(client, app)
    with app.app_context():
        poll = Poll(question="Choose", duration_days=1, duration_hours=0,
                    duration_minutes=0, user_id=user_id)
        db.session.add(poll)
        db.session.commit()
        options = [PollOption(option_text=text, poll_id=poll.id) for text in ("A", "B")]
        db.session.add_all(options)
        db.session.commit()
        db.session.add(PollVote(poll_id=poll.id, user_id=user_id, option_id=options[0].id))
        db.session.commit()
        db.session.add(PollVote(poll_id=poll.id, user_id=user_id, option_id=options[1].id))

        with pytest.raises(IntegrityError):
            db.session.commit()
        db.session.rollback()


def test_vote_option_must_belong_to_route_poll(client, app):
    user_id = create_logged_in_user(client, app)
    with app.app_context():
        polls = [Poll(question=q, duration_days=1, duration_hours=0,
                      duration_minutes=0, user_id=user_id) for q in ("One", "Two")]
        db.session.add_all(polls)
        db.session.commit()
        option = PollOption(option_text="Second poll option", poll_id=polls[1].id)
        db.session.add(option)
        db.session.commit()
        first_poll_id, option_id = polls[0].id, option.id

    response = client.post(f"/vote_poll/{first_poll_id}", data={"option_id": option_id})

    assert response.status_code == 404
    with app.app_context():
        assert PollVote.query.count() == 0
        assert db.session.get(PollOption, option_id).votes == 0
