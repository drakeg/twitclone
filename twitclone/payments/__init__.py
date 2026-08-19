"""Stripe-backed billing workflows."""

from flask import Blueprint

payments_blueprint = Blueprint("payments", __name__)

from twitclone.payments import routes  # noqa: E402,F401

__all__ = ["payments_blueprint"]
