"""TwitClone application factory.

This factory provides one supported construction path while ``app.py`` remains
as a transitional startup and compatibility module.
"""

from __future__ import annotations

from pathlib import Path

import click
from flask import Flask

from config import Config


def create_app(config_object: type[Config] = Config) -> Flask:
    """Create and configure the TwitClone Flask application."""

    config_object.validate()

    import app as legacy_app

    from twitclone.admin import admin_blueprint
    from twitclone.auth import auth_blueprint
    from twitclone.billing import ensure_default_plans
    from twitclone.bookmarks import bookmarks_blueprint
    from twitclone.community import community_blueprint
    from twitclone.demo import DEMO_PASSWORD, seed_demo_content
    from twitclone.discovery import discovery_blueprint
    from twitclone.deployment_preflight import (
        DeploymentPreflightError,
        run_deployment_preflight,
    )
    from twitclone.extensions import db
    from twitclone.media_migration import migrate_media_directory
    from twitclone.media_storage import init_media_storage
    from twitclone.messaging import messaging_blueprint
    from twitclone.models import User
    from twitclone.notifications import notifications_blueprint
    from twitclone.observability import configure_observability
    from twitclone.payments import payments_blueprint
    from twitclone.polls import polls_blueprint
    from twitclone.profiles import profiles_blueprint
    from twitclone.resources import resources_blueprint
    from twitclone.timeline import timeline_blueprint
    from twitclone.utils import bind_legacy_module

    bind_legacy_module(legacy_app)
    flask_app = legacy_app.app
    scheduler = legacy_app.scheduler
    flask_app.config.from_object(config_object)
    init_media_storage(flask_app)
    configure_observability(flask_app)

    for blueprint in (
        auth_blueprint,
        timeline_blueprint,
        messaging_blueprint,
        polls_blueprint,
        notifications_blueprint,
        profiles_blueprint,
        discovery_blueprint,
        bookmarks_blueprint,
        resources_blueprint,
        admin_blueprint,
        community_blueprint,
        payments_blueprint,
    ):
        if blueprint.name not in flask_app.blueprints:
            flask_app.register_blueprint(blueprint)

    if "make-super-admin" not in flask_app.cli.commands:
        @flask_app.cli.command("make-super-admin")
        @click.argument("email")
        def make_super_admin(email):
            """Promote an existing account to Ripple super-admin by email."""
            user = User.query.filter(db.func.lower(User.email) == email.lower()).first()
            if user is None:
                raise click.ClickException("No Ripple user exists with that email address.")
            user.is_admin = True
            user.is_super_admin = True
            db.session.commit()
            click.echo(f"@{user.username} is now a Ripple super-admin.")

    if "seed-demo-content" not in flask_app.cli.commands:
        @flask_app.cli.command("seed-demo-content")
        @click.option("--seed", type=int, default=2026, show_default=True)
        def seed_demo_content_command(seed):
            """Create sample users and activity for local development/demo use."""
            if flask_app.config.get("ENVIRONMENT") == "production":
                raise click.ClickException("Demo content cannot be seeded in production.")
            result = seed_demo_content(seed=seed)
            click.echo("Demo content ready: " f"{result['users']} users, {result['posts']} posts, " f"{result['follows']} follows, {result['reposts']} reposts, " f"{result['quotes']} quotes created.")
            click.echo(f"Demo account password: {DEMO_PASSWORD}")

    if "seed-billing-plans" not in flask_app.cli.commands:
        @flask_app.cli.command("seed-billing-plans")
        def seed_billing_plans_command():
            """Create/update Ripple's provider-neutral plan catalog."""
            ensure_default_plans()
            click.echo("Ripple billing plan catalog is ready.")

    if "migrate-media-to-s3" not in flask_app.cli.commands:
        @flask_app.cli.command("migrate-media-to-s3")
        @click.option("--source", type=click.Path(path_type=Path), default=None)
        @click.option("--dry-run", is_flag=True, help="Report work without writing objects.")
        @click.option("--overwrite", is_flag=True, help="Replace destination objects whose content differs.")
        def migrate_media_to_s3(source, dry_run, overwrite):
            """Copy existing filesystem media into configured S3 storage."""
            if flask_app.config.get("MEDIA_STORAGE_BACKEND") != "s3":
                raise click.ClickException("Set MEDIA_STORAGE_BACKEND=s3 before migrating media.")
            source = source or Path(flask_app.config["UPLOAD_FOLDER"])
            try:
                result = migrate_media_directory(
                    source,
                    flask_app.extensions["media_storage"],
                    dry_run=dry_run,
                    overwrite=overwrite,
                )
            except (OSError, RuntimeError, ValueError) as exc:
                raise click.ClickException(str(exc)) from exc
            click.echo(
                f"Media migration {'plan' if dry_run else 'complete'}: "
                f"{result.discovered} discovered, {result.copied} copied, "
                f"{result.unchanged} unchanged, {result.conflicts} conflicts, "
                f"{result.bytes_copied} bytes {'planned' if dry_run else 'written'}."
            )
            if result.conflicts:
                raise click.ClickException(
                    "Destination conflicts were not overwritten. Review them and rerun with --overwrite only if approved."
                )

    if "deployment-preflight" not in flask_app.cli.commands:
        @flask_app.cli.command("deployment-preflight")
        def deployment_preflight():
            """Verify production database, schema, and media readiness."""
            if flask_app.config.get("ENVIRONMENT") != "production":
                raise click.ClickException(
                    "Set TWITCLONE_ENV=production before running deployment preflight."
                )
            try:
                result = run_deployment_preflight(
                    database_session=db.session,
                    media_storage=flask_app.extensions["media_storage"],
                    migrations_directory=Path(flask_app.root_path) / "migrations",
                )
            except DeploymentPreflightError as exc:
                raise click.ClickException(str(exc)) from exc
            click.echo(f"Database: {result.database}")
            click.echo(f"Migrations: current ({result.migrations})")
            click.echo(f"Media: {result.media}")
            click.echo("Deployment preflight passed.")

    if not flask_app.config["SCHEDULER_ENABLED"] and scheduler.running:
        scheduler.shutdown(wait=False)

    return flask_app


__all__ = ["create_app"]
