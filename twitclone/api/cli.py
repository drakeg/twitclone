"""Operator-managed API credential lifecycle commands."""

from datetime import timedelta

import click

from twitclone.api import api_blueprint
from twitclone.api.credentials import (
    ApiCredential,
    MAX_CREDENTIAL_LIFETIME_DAYS,
    _utcnow,
    issue_api_credential,
    revoke_api_credential,
)
from twitclone.extensions import db
from twitclone.models import User


def _user_by_email(email):
    user = User.query.filter(db.func.lower(User.email) == email.strip().lower()).first()
    if user is None:
        raise click.ClickException("No Ripple user exists with that email address.")
    return user


@api_blueprint.cli.command("credential-create")
@click.argument("email")
@click.option("--label", required=True, help="Human-readable credential label.")
@click.option("--days", type=click.IntRange(1, MAX_CREDENTIAL_LIFETIME_DAYS), default=90, show_default=True)
def credential_create(email, label, days):
    """Create a posts:read bearer credential and display its token once."""
    user = _user_by_email(email)
    credential, raw_token = issue_api_credential(
        user_id=user.id,
        label=label,
        scopes={"posts:read"},
        expires_at=_utcnow() + timedelta(days=days),
    )
    db.session.commit()
    click.echo(f"Credential {credential.id} created for @{user.username}; expires {credential.expires_at.isoformat()}Z.")
    click.echo("Store this token securely; Ripple will not display it again:")
    click.echo(raw_token)


@api_blueprint.cli.command("credential-list")
@click.argument("email")
def credential_list(email):
    """List credential metadata without exposing bearer secrets."""
    user = _user_by_email(email)
    rows = ApiCredential.query.filter_by(user_id=user.id).order_by(ApiCredential.id.asc()).all()
    if not rows:
        click.echo("No API credentials.")
        return
    now = _utcnow()
    for row in rows:
        if row.revoked_at is not None:
            status = "revoked"
        elif row.expires_at <= now:
            status = "expired"
        else:
            status = "active"
        click.echo(
            f"{row.id}\t{status}\t{row.label}\t{row.token_prefix}…\t"
            f"{row.scopes}\texpires={row.expires_at.isoformat()}Z\t"
            f"last_used={row.last_used_at.isoformat() + 'Z' if row.last_used_at else 'never'}"
        )


@api_blueprint.cli.command("credential-revoke")
@click.argument("email")
@click.argument("credential_id", type=int)
def credential_revoke(email, credential_id):
    """Revoke one credential owned by the selected Ripple user."""
    user = _user_by_email(email)
    credential = ApiCredential.query.filter_by(id=credential_id, user_id=user.id).first()
    if credential is None:
        raise click.ClickException("Credential was not found for that user.")
    revoke_api_credential(credential)
    click.echo(f"Credential {credential.id} revoked.")
