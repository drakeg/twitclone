"""Sprint 13 Story 13.5 community contribution context coverage."""

from twitclone.contribution_models import ConstructiveContribution
from twitclone.extensions import db
from twitclone.models import Tweet, User
from twitclone.spaces.contribution import build_space_contribution_context
from twitclone.spaces.models import Space, SpaceMembership, SpacePost


def _fixture(app):
    with app.app_context():
        owner = User(username="context_owner", email="context-owner@example.com", password="hash")
        author = User(username="context_author", email="context-author@example.com", password="hash")
        recognizer = User(username="context_recognizer", email="context-recognizer@example.com", password="hash")
        outsider = User(username="context_outsider", email="context-outsider@example.com", password="hash")
        db.session.add_all([owner, author, recognizer, outsider]); db.session.flush()
        space = Space(slug="context-space", name="Context Space", description="Contribution context.", owner_id=owner.id)
        db.session.add(space); db.session.flush()
        db.session.add_all([
            SpaceMembership(space_id=space.id, user_id=owner.id, role="owner"),
            SpaceMembership(space_id=space.id, user_id=author.id, role="member"),
            SpaceMembership(space_id=space.id, user_id=recognizer.id, role="member"),
        ])
        visible = Tweet(content="visible contribution", user_id=author.id)
        hidden = Tweet(content="hidden contribution", user_id=author.id)
        removed = Tweet(content="removed contribution", user_id=author.id, is_removed=True)
        db.session.add_all([visible, hidden, removed]); db.session.flush()
        db.session.add_all([
            SpacePost(space_id=space.id, tweet_id=visible.id),
            SpacePost(space_id=space.id, tweet_id=hidden.id, is_hidden=True),
            SpacePost(space_id=space.id, tweet_id=removed.id),
        ]); db.session.flush()
        db.session.add_all([
            ConstructiveContribution(user_id=recognizer.id, tweet_id=visible.id, signal="helpful"),
            ConstructiveContribution(user_id=recognizer.id, tweet_id=visible.id, signal="context"),
            ConstructiveContribution(user_id=outsider.id, tweet_id=visible.id, signal="thoughtful"),
            ConstructiveContribution(user_id=author.id, tweet_id=visible.id, signal="thoughtful"),
            ConstructiveContribution(user_id=recognizer.id, tweet_id=hidden.id, signal="helpful"),
            ConstructiveContribution(user_id=recognizer.id, tweet_id=removed.id, signal="helpful"),
        ])
        db.session.commit()
        return space.id, author.id, recognizer.id


def test_context_counts_only_member_to_member_visible_space_evidence(app):
    space_id, author_id, _ = _fixture(app)
    with app.app_context():
        context = build_space_contribution_context(db.session.get(Space, space_id))
        assert context["signal_total"] == 2
        assert context["recognized_posts"] == 1
        assert context["unique_recognizers"] == 1
        assert len(context["members"]) == 1
        summary = context["members"][0]
        assert summary["user"].id == author_id
        assert summary["signal_counts"] == {"helpful": 1, "thoughtful": 0, "context": 1}
        assert summary["recognized_posts"] == 1
        assert summary["unique_recognizers"] == 1


def test_context_updates_when_recognizer_leaves_space(app):
    space_id, _, recognizer_id = _fixture(app)
    with app.app_context():
        membership = SpaceMembership.query.filter_by(space_id=space_id, user_id=recognizer_id).one()
        db.session.delete(membership); db.session.commit()
        context = build_space_contribution_context(db.session.get(Space, space_id))
        assert context == {"members": [], "signal_total": 0, "recognized_posts": 0, "unique_recognizers": 0}


def test_space_page_explains_context_is_not_ranking(client, app):
    _fixture(app)
    response = client.get("/spaces/context-space")
    assert response.status_code == 200
    assert b"Constructive contributions in this space" in response.data
    assert b"context, not a leaderboard or reputation score" in response.data
    assert b"Members are shown alphabetically" in response.data
    assert b"Helpful 1" in response.data
    assert b"Useful context 1" in response.data
