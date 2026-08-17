"""Dedicated scheduled-post worker process."""

import logging
import signal
import threading

from config import Config
from twitclone import create_app
from twitclone.scheduling import publish_due_tweets


log = logging.getLogger("twitclone.worker")


def main():
    app = create_app()
    stop = threading.Event()
    signal.signal(signal.SIGTERM, lambda *_: stop.set())
    signal.signal(signal.SIGINT, lambda *_: stop.set())
    while not stop.is_set():
        with app.app_context():
            published = publish_due_tweets()
        if published:
            log.info(
                "scheduled_tweets_published",
                extra={"event": "scheduled_tweets_published", "published_count": published},
            )
        stop.wait(Config.SCHEDULER_INTERVAL_SECONDS)


if __name__ == "__main__":
    main()
