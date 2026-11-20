"""Development-only demo users and public content for Ripple."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
import random

from flask import current_app

from twitclone.community.routes import COMMUNITY_GUIDELINES_VERSION
from twitclone.extensions import bcrypt, db
from twitclone.models import Follows, Quote, Retweet, Tweet, User
from twitclone.spaces.models import (
    Space,
    SpaceMembership,
    SpaceModerationAction,
    SpaceModerationAppeal,
    SpacePost,
)

DEMO_PASSWORD = "Passw0rd!"
DEMO_USERS = (
    ("trailbound", "trailbound@example.test", "Weekend hikes, road trips, and places worth stopping for."),
    ("bytebloom", "bytebloom@example.test", "Linux, Python, automation, and the occasional broken build."),
    ("cityplate", "cityplate@example.test", "Good food, hidden restaurants, and strong opinions about breakfast."),
    ("liftandlive", "liftandlive@example.test", "Training, consistency, and making fitness fit real life."),
    ("lensandlight", "lensandlight@example.test", "Photos, small adventures, and learning to notice more."),
    ("gardenpatch", "gardenpatch@example.test", "Growing food, hydroponics, herbs, and experiments that mostly work."),
    ("campfirecode", "campfirecode@example.test", "Remote work, RV life, and code written near a campfire."),
    ("historywalks", "historywalks@example.test", "Old places, local stories, museums, and roadside history."),
)
DEMO_SPACE_SLUG = "roadside-creators-club"
DEMO_SPACE_NAME = "Roadside Creators Club"
DEMO_SPACE_DESCRIPTION = (
    "A sample member community for creators and remote workers sharing ideas from the road."
)
DEMO_SPACE_OWNER = "campfirecode"
DEMO_SPACE_MODERATOR = "bytebloom"
DEMO_SPACE_POSTS = (
    "Working from the road today. Hotspot is behaving, coffee is strong, deploy is green. #remotework #rv",
    "There is a very specific kind of confidence that comes from fixing production from a campground. #devops #rv",
    "@trailbound next road trip needs a diner rule: local place, full parking lot, pie in a glass case. #roadtrip #food",
    "Small-town museums continue to be wildly underrated. #travel #history",
)

POST_IDEAS = (
    ("trailbound", "Found a quiet trail this morning and had the whole overlook to myself. #hiking #weekend"),
    ("bytebloom", "Finally automated the thing I kept saying only takes five minutes. It took three hours. #python #automation"),
    ("cityplate", "Breakfast sandwiches should be judged mostly by whether they survive the first bite. #food"),
    ("liftandlive", "A short workout you actually do beats the perfect workout you keep postponing. #fitness"),
    ("lensandlight", "Golden hour lasted about twelve minutes today, but it was worth chasing. #photography"),
    ("gardenpatch", "First basil harvest from the hydroponic setup. Tiny win, excellent smell. #gardening #hydroponics"),
    ("campfirecode", "Working from the road today. Hotspot is behaving, coffee is strong, deploy is green. #remotework #rv"),
    ("historywalks", "The best local-history stops are often the ones with one small sign and a story nobody expects. #history"),
    ("trailbound", "@lensandlight you would have loved the fog rolling through the valley this morning. #outdoors"),
    ("bytebloom", "@campfirecode I finally tried that shell shortcut. I should have listened sooner. #linux"),
    ("cityplate", "@trailbound next road trip needs a diner rule: local place, full parking lot, pie in a glass case. #roadtrip #food"),
    ("liftandlive", "@gardenpatch fresh herbs make meal prep dramatically less boring. #nutrition #fitness"),
    ("lensandlight", "@historywalks old buildings are much more fun to photograph when somebody knows the story behind them. #photography #history"),
    ("gardenpatch", "Trying cilantro again even though cilantro and I have a complicated history. #gardening"),
    ("campfirecode", "There is a very specific kind of confidence that comes from fixing production from a campground. #devops #rv"),
    ("historywalks", "Small-town museums continue to be wildly underrated. #travel #history"),
)


def _naive_utcnow() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


def seed_demo_content(*, seed: int = 2026) -> dict[str, int]:
    if current_app.config.get("ENVIRONMENT") == "production":
        raise RuntimeError("Demo content cannot be seeded in production.")
    rng = random.Random(seed)
    password_hash = bcrypt.generate_password_hash(DEMO_PASSWORD).decode("utf-8")
    users = {}
    created_users = created_posts = created_follows = created_reposts = created_quotes = 0
    created_spaces = created_space_memberships = created_space_posts = 0
    created_space_moderation_actions = created_space_appeals = 0
    now = _naive_utcnow()
    for username, email, bio in DEMO_USERS:
        user = User.query.filter_by(username=username).first()
        if user is None:
            user = User(username=username, email=email, password=password_hash, bio=bio)
            db.session.add(user); db.session.flush(); created_users += 1
        if user.community_guidelines_version != COMMUNITY_GUIDELINES_VERSION:
            user.community_guidelines_version = COMMUNITY_GUIDELINES_VERSION
            user.community_guidelines_accepted_at = now
        users[username] = user
    posts = []; shuffled = list(POST_IDEAS); rng.shuffle(shuffled)
    for index, (username, content) in enumerate(shuffled):
        author = users[username]; tweet = Tweet.query.filter_by(user_id=author.id, content=content).first()
        if tweet is None:
            tweet = Tweet(content=content, user_id=author.id, timestamp=now - timedelta(minutes=(len(shuffled)-index)*19)); db.session.add(tweet); db.session.flush(); created_posts += 1
        posts.append(tweet)
    user_list = list(users.values())
    for follower in user_list:
        for followed in rng.sample([u for u in user_list if u.id != follower.id], k=2):
            if db.session.get(Follows, (follower.id, followed.id)) is None:
                db.session.add(Follows(follower_id=follower.id, followed_id=followed.id)); created_follows += 1
    for user in rng.sample(user_list, k=min(4, len(user_list))):
        target = rng.choice([tweet for tweet in posts if tweet.user_id != user.id])
        age_minutes = rng.randint(3, 90)
        if Retweet.query.filter_by(user_id=user.id, tweet_id=target.id).first() is None:
            db.session.add(Retweet(user_id=user.id, tweet_id=target.id, timestamp=now-timedelta(minutes=age_minutes))); created_reposts += 1
    quote_texts = ("This is exactly the kind of thing I come here for.", "Adding this to the weekend list.", "Strong agreement from me.")
    for user in rng.sample(user_list, k=min(3, len(user_list))):
        target = rng.choice([tweet for tweet in posts if tweet.user_id != user.id]); content = rng.choice(quote_texts)
        age_minutes = rng.randint(2, 75)
        if Quote.query.filter_by(user_id=user.id, tweet_id=target.id, content=content).first() is None:
            db.session.add(Quote(user_id=user.id, tweet_id=target.id, content=content, timestamp=now-timedelta(minutes=age_minutes))); created_quotes += 1

    demo_space = Space.query.filter_by(slug=DEMO_SPACE_SLUG).first()
    if demo_space is None:
        demo_space = Space(
            slug=DEMO_SPACE_SLUG,
            name=DEMO_SPACE_NAME,
            description=DEMO_SPACE_DESCRIPTION,
            owner_id=users[DEMO_SPACE_OWNER].id,
            created_at=now - timedelta(days=45),
        )
        db.session.add(demo_space)
        db.session.flush()
        created_spaces += 1

    for username, user in users.items():
        membership = SpaceMembership.query.filter_by(
            space_id=demo_space.id,
            user_id=user.id,
        ).first()
        if membership is None:
            if username == DEMO_SPACE_OWNER:
                role = "owner"
                joined_at = now - timedelta(days=45)
            elif username == DEMO_SPACE_MODERATOR:
                role = "moderator"
                joined_at = now - timedelta(days=30)
            else:
                role = "member"
                joined_at = now - timedelta(days=rng.randint(1, 24))
            db.session.add(
                SpaceMembership(
                    space_id=demo_space.id,
                    user_id=user.id,
                    role=role,
                    joined_at=joined_at,
                )
            )
            created_space_memberships += 1

    demo_space_rows = []
    for index, content in enumerate(DEMO_SPACE_POSTS):
        tweet = Tweet.query.filter_by(content=content).first()
        if tweet is None:
            continue
        row = SpacePost.query.filter_by(tweet_id=tweet.id).first()
        if row is None:
            row = SpacePost(
                space_id=demo_space.id,
                tweet_id=tweet.id,
                created_at=now - timedelta(days=index + 1),
                is_hidden=index == len(DEMO_SPACE_POSTS) - 1,
                hidden_at=(now - timedelta(hours=6)) if index == len(DEMO_SPACE_POSTS) - 1 else None,
                hidden_by_id=users[DEMO_SPACE_MODERATOR].id if index == len(DEMO_SPACE_POSTS) - 1 else None,
                hidden_reason="Demo moderation example for operator review." if index == len(DEMO_SPACE_POSTS) - 1 else None,
            )
            db.session.add(row)
            db.session.flush()
            created_space_posts += 1
        if row.space_id == demo_space.id:
            demo_space_rows.append(row)

    hidden_demo_row = next((row for row in demo_space_rows if row.is_hidden), None)
    if hidden_demo_row is not None:
        action = SpaceModerationAction.query.filter_by(
            space_id=demo_space.id,
            action_type="hide_post",
            target_type="post",
            target_id=hidden_demo_row.id,
        ).first()
        if action is None:
            action = SpaceModerationAction(
                space_id=demo_space.id,
                actor_id=users[DEMO_SPACE_MODERATOR].id,
                action_type="hide_post",
                target_type="post",
                target_id=hidden_demo_row.id,
                affected_user_id=hidden_demo_row.tweet.user_id,
                reason="Demo moderation example for operator review.",
                created_at=now - timedelta(hours=6),
            )
            db.session.add(action)
            db.session.flush()
            created_space_moderation_actions += 1

        appeal = SpaceModerationAppeal.query.filter_by(action_id=action.id).first()
        if appeal is None:
            db.session.add(
                SpaceModerationAppeal(
                    space_id=demo_space.id,
                    action_id=action.id,
                    requester_id=hidden_demo_row.tweet.user_id,
                    rationale="Demo appeal: please review this local moderation decision.",
                    submitted_at=now - timedelta(hours=4),
                )
            )
            created_space_appeals += 1

    db.session.commit()
    return {
        "users": created_users,
        "posts": created_posts,
        "follows": created_follows,
        "reposts": created_reposts,
        "quotes": created_quotes,
        "spaces": created_spaces,
        "space_memberships": created_space_memberships,
        "space_posts": created_space_posts,
        "space_moderation_actions": created_space_moderation_actions,
        "space_appeals": created_space_appeals,
    }


__all__ = [
    "DEMO_PASSWORD",
    "DEMO_USERS",
    "DEMO_SPACE_SLUG",
    "DEMO_SPACE_NAME",
    "seed_demo_content",
]
