"""Creator sustainability analytics routes for Sprint 15."""

from flask import render_template, request
from flask_login import current_user, login_required

from twitclone.analytics_tracking import record_sustainability_page_visit
from twitclone.creator_memberships import CreatorMembershipOffering
from twitclone.creator_support import CreatorSupportProfile
from twitclone.models import User
from twitclone.profiles import profiles_blueprint
from twitclone.sustainability_analytics import SUPPORT_PAGE, build_sustainability_summary


@profiles_blueprint.after_app_request
def record_creator_support_page(response):
    """Measure successful public support-page views without changing its route."""
    if response.status_code == 200 and request.endpoint == "creator_support":
        username = (request.view_args or {}).get("username")
        user = User.query.filter_by(username=username).first() if username else None
        if user is not None:
            record_sustainability_page_visit(user, SUPPORT_PAGE)
    return response


@login_required
def creator_sustainability_analytics():
    summary = build_sustainability_summary(current_user.id, days=request.args.get("days", 30, type=int) or 30)
    support_profile = CreatorSupportProfile.query.filter_by(user_id=current_user.id).first()
    membership_offering = CreatorMembershipOffering.query.filter_by(user_id=current_user.id).first()
    return render_template(
        "creator_sustainability_analytics.html",
        summary=summary,
        support_profile=support_profile,
        membership_offering=membership_offering,
    )


@profiles_blueprint.record_once
def register_sustainability_routes(state):
    state.app.add_url_rule(
        "/creator/support/analytics",
        endpoint="creator_sustainability_analytics",
        view_func=creator_sustainability_analytics,
    )
