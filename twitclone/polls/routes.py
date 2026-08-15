"""Poll creation and voting routes."""

from flask import flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from sqlalchemy.exc import IntegrityError

from forms import PollForm
from twitclone.extensions import db
from twitclone.models import Poll, PollOption, PollVote
from twitclone.polls import polls_blueprint


@login_required
def create_poll():
    form = PollForm()
    if form.validate_on_submit():
        poll = Poll(
            question=form.question.data,
            duration_days=form.duration_days.data,
            duration_hours=form.duration_hours.data,
            duration_minutes=form.duration_minutes.data,
            user_id=current_user.id,
        )
        db.session.add(poll)
        db.session.commit()

        for option in form.options.data:
            poll_option = PollOption(
                option_text=option["option_text"], poll_id=poll.id
            )
            db.session.add(poll_option)
        db.session.commit()

        flash("Poll created successfully!", "success")
        return redirect(url_for("index"))

    return render_template("create_poll.html", form=form)


@login_required
def vote_poll(poll_id):
    option_id = request.form.get("option_id")
    if not option_id:
        flash("You must select an option to vote", "warning")
        return redirect(url_for("index"))

    Poll.query.get_or_404(poll_id)
    option = PollOption.query.filter_by(id=option_id, poll_id=poll_id).first_or_404()

    vote = PollVote.query.filter_by(
        poll_id=poll_id, user_id=current_user.id
    ).first()
    if vote:
        flash("You have already voted in this poll", "warning")
    else:
        new_vote = PollVote(
            poll_id=poll_id, user_id=current_user.id, option_id=option_id
        )
        option.votes += 1
        db.session.add(new_vote)
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            flash("You have already voted in this poll", "warning")
        else:
            flash("Your vote has been recorded", "success")

    return redirect(url_for("index"))


@polls_blueprint.record_once
def register_poll_routes(state):
    """Register routes while retaining existing endpoint names."""
    state.app.add_url_rule(
        "/create_poll",
        endpoint="create_poll",
        view_func=create_poll,
        methods=["GET", "POST"],
    )
    state.app.add_url_rule(
        "/vote_poll/<int:poll_id>",
        endpoint="vote_poll",
        view_func=vote_poll,
        methods=["POST"],
    )
