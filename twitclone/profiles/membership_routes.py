"""Creator membership offering routes for Sprint 15."""

from flask import abort, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from twitclone.analytics_tracking import record_sustainability_page_visit
from twitclone.creator_memberships import (
    CreatorMembershipOffering,
    MEMBERSHIP_BENEFITS,
    normalized_membership_description,
    normalized_membership_name,
    serialize_benefit_keys,
)
from twitclone.creator_support import CreatorSupportProfile
from twitclone.extensions import db
from twitclone.models import User
from twitclone.profiles import profiles_blueprint
from twitclone.sustainability_analytics import MEMBERSHIP_PAGE


@login_required
def creator_membership_settings():
    offering = CreatorMembershipOffering.query.filter_by(user_id=current_user.id).first()
    if request.method == "POST":
        enabled = request.form.get("enabled") == "1"
        name = normalized_membership_name(request.form.get("name"))
        description = normalized_membership_description(request.form.get("description"))
        benefit_values = request.form.getlist("benefits")
        serialized_benefits = serialize_benefit_keys(benefit_values)

        if enabled and not name:
            flash("Add a membership name before publishing the offering.", "danger")
            return render_template(
                "creator_membership_settings.html",
                offering=offering,
                membership_benefits=MEMBERSHIP_BENEFITS,
            )
        if enabled and not description:
            flash("Add a membership description before publishing the offering.", "danger")
            return render_template(
                "creator_membership_settings.html",
                offering=offering,
                membership_benefits=MEMBERSHIP_BENEFITS,
            )
        if enabled and not serialized_benefits:
            flash("Choose at least one supported membership benefit before publishing.", "danger")
            return render_template(
                "creator_membership_settings.html",
                offering=offering,
                membership_benefits=MEMBERSHIP_BENEFITS,
            )

        if offering is None:
            offering = CreatorMembershipOffering(user_id=current_user.id)
            db.session.add(offering)
        offering.enabled = enabled
        offering.name = name
        offering.description = description
        offering.benefits = serialized_benefits
        db.session.commit()
        flash("Membership offering updated.", "success")
        return redirect(url_for("creator_membership_settings"))

    return render_template(
        "creator_membership_settings.html",
        offering=offering,
        membership_benefits=MEMBERSHIP_BENEFITS,
    )


def creator_membership(username):
    user = User.query.filter_by(username=username).first_or_404()
    support_profile = CreatorSupportProfile.query.filter_by(user_id=user.id, enabled=True).first()
    offering = CreatorMembershipOffering.query.filter_by(user_id=user.id, enabled=True).first()
    if support_profile is None or offering is None:
        abort(404)
    record_sustainability_page_visit(user, MEMBERSHIP_PAGE)
    return render_template("creator_membership.html", user=user, offering=offering)


@profiles_blueprint.record_once
def register_membership_routes(state):
    state.app.add_url_rule(
        "/creator/membership",
        endpoint="creator_membership_settings",
        view_func=creator_membership_settings,
        methods=["GET", "POST"],
    )
    state.app.add_url_rule(
        "/support/<username>/membership",
        endpoint="creator_membership",
        view_func=creator_membership,
    )
