"""Stripe-backed billing workflows."""

from flask import Blueprint

billing_blueprint = Blueprint("billing", __name__)

from twitclone.billing import routes  # noqa: E402,F401

__all__ = ["billing_blueprint"]
