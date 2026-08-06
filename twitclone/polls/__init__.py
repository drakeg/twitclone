"""Polls Blueprint."""

from flask import Blueprint

polls_blueprint = Blueprint("polls", __name__)

from twitclone.polls import routes  # noqa: E402, F401

__all__ = ["polls_blueprint"]
