"""Development-only demo users and public content for Ripple."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
import random

from flask import current_app

from twitclone.extensions import bcrypt, db
from twitclone.models import Follows, Quote, Retweet, Tweet, User

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
    """Create idempotent development/test demo accounts and social activity."""
    if current_app.config.get("ENVIRONMENT") == "production":
        raise RuntimeError("Demo content cannot be seeded in production.")

    rng = random.Random(seed)
    password_hash = bcrypt.generate_password_hash(DEMO_PASSWORD).decode("utf-8")
    users: dict[str, User] = {}
    created_users = 0
    created_posts = 0
    created_follows = 0
    created_reposts = 0
    created_quotes = 0

    for username, email, bio in DEMO_USERS:
        user = User.query.filter_by(username=username).first()
        if user is None:
            user = User(username=username, email=email, password=password_hash, bio=bio)
            db.session.add(user)
            db.session.flush()
            created_users += 1
        users[username] = user

    now = _naive_utcnow()
    posts: list[Tweet] = []
    shuffled = list(POST_IDEAS)
    rng.shuffle(shuffled)
    for index, (username, content) in enumerate(shuffled):
        author = users[username]
        tweet = Tweet.query.filter_by(user_id=author.id, content=content).first()
        if tweet is None:
            tweet = Tweet(
                content=content,
                user_id=author.id,
                timestamp=now - timedelta(minutes=(len(shuffled) - index) * 19),
            )
            db.session.add(tweet)
            db.session.flush()
            created_posts += 1
        posts.append(tweet)

    user_list = list(users.values())
    for follower in user_list:
        candidates = [user for user in user_list if user.id != follower.id]
        for followed in rng.sample(candidates, k=2):
            existing = db.session.get(Follows, (follower.id, followed.id))
            if existing is None:
                db.session.add(Follows(follower_id=follower.id, followed_id=followed.id))
                created_follows += 1

    for user in rng.sample(user_list, k=min(4, len(user_list))):
        candidates = [tweet for tweet in posts if tweet.user_id != user.id]
        target = rng.choice(candidates)
        if Retweet.query.filter_by(user_id=user.id, tweet_id=target.id).first() is None:
            db.session.add(
                Retweet(
                    user_id=user.id,
                    tweet_id=target.id,
                    timestamp=now - timedelta(minutes=rng.randint(3, 90)),
                )
            )
            created_reposts += 1

    quote_texts = (
        "This is exactly the kind of thing I come here for.",
        "Adding this to the weekend list.",
        "Strong agreement from me.",
    )
    for user in rng.sample(user_list, k=min(3, len(user_list))):
        candidates = [tweet for tweet in posts if tweet.user_id != user.id]
        target = rng.choice(candidates)
        content = rng.choice(quote_texts)
        if Quote.query.filter_by(user_id=user.id, tweet_id=target.id, content=content).first() is None:
            db.session.add(
                Quote(
                    user_id=user.id,
                    tweet_id=target.id,
                    content=content,
                    timestamp=now - timedelta(minutes=rng.randint(2, 75)),
                )
            )
            created_quotes += 1

    db.session.commit()
    return {
        "users": created_users,
        "posts": created_posts,
        "follows": created_follows,
        "reposts": created_reposts,
        "quotes": created_quotes,
    }


__all__ = ["DEMO_PASSWORD", "DEMO_USERS", "seed_demo_content"]
