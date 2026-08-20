"""Profile and social graph routes."""

import re
from collections import Counter
from pathlib import Path

from flask import current_app, flash, jsonify, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from twitclone.analytics_tracking import record_profile_visit, snapshot_followers
from twitclone.extensions import db
from twitclone.models import Notification, Quote, Retweet, Tweet, User
from twitclone.profiles import profiles_blueprint
from twitclone.timeline.media import prepare_image_upload

PROFILE_THEMES = {'ripple':'Ripple Blue','sunset':'Sunset','forest':'Forest','violet':'Violet','slate':'Slate'}
HASHTAG_RE = re.compile(r'(?<!\w)#([A-Za-z0-9_]+)')


def _store_profile_banner(upload):
    error, generated_name = prepare_image_upload(upload)
    if error: return error, None
    banner_name = f"banner_{generated_name}"; upload.save(Path(current_app.config['UPLOAD_FOLDER']) / banner_name); return None, banner_name


@login_required
def follow(username):
    user = User.query.filter_by(username=username).first()
    if user and user not in current_user.followed:
        current_user.followed.append(user); db.session.commit(); snapshot_followers(user); db.session.add(Notification(user_id=user.id, message=f"{current_user.username} followed you")); db.session.commit(); return jsonify({'status':'success','message':f'You are now following {username}.'})
    if user: return jsonify({'status':'success','message':f'You are now following {username}.'})
    return jsonify({'status':'error','message':'User not found.'})


@login_required
def unfollow(username):
    user = User.query.filter_by(username=username).first()
    if user and user in current_user.followed:
        current_user.followed.remove(user); db.session.commit(); snapshot_followers(user); db.session.add(Notification(user_id=user.id, message=f"{current_user.username} unfollowed you")); db.session.commit(); return jsonify({'status':'success','message':f'You have unfollowed {username}.'})
    if user: return jsonify({'status':'success','message':f'You have unfollowed {username}.'})
    return jsonify({'status':'error','message':'User not found.'})


@login_required
def profile(username):
    user = User.query.filter_by(username=username).first_or_404(); record_profile_visit(user); is_following = user in current_user.followed; premium_profile_active = user.has_entitlement('ripple_plus')
    return render_template('profile.html', user=user, is_following=is_following, premium_profile_active=premium_profile_active)


def _analytics_counts(user):
    tweets = Tweet.query.filter_by(user_id=user.id, is_removed=False).all(); tweet_ids = [tweet.id for tweet in tweets]
    reposts = Retweet.query.filter(Retweet.tweet_id.in_(tweet_ids)).count() if tweet_ids else 0
    quotes = Quote.query.filter(Quote.tweet_id.in_(tweet_ids), Quote.is_removed.is_(False)).count() if tweet_ids else 0
    return tweets, {'posts':len(tweets),'followers':user.followers.count(),'following':user.followed.count(),'reposts_received':reposts,'quotes_received':quotes}


@login_required
def analytics():
    if not (current_user.has_entitlement('ripple_plus') or current_user.has_entitlement('creator_pro')):
        flash('Analytics are included with Ripple+ and Creator Pro.', 'info'); return redirect(url_for('payments.billing_home'))
    _, stats = _analytics_counts(current_user)
    return render_template('analytics.html', stats=stats)


@login_required
def creator_analytics():
    if not current_user.has_entitlement('creator_pro'):
        flash('Advanced creator analytics are included with Creator Pro.', 'info'); return redirect(url_for('payments.billing_home'))
    tweets, stats = _analytics_counts(current_user); tweet_ids = [tweet.id for tweet in tweets]
    repost_counts = Counter(row[0] for row in db.session.query(Retweet.tweet_id).filter(Retweet.tweet_id.in_(tweet_ids)).all()) if tweet_ids else Counter()
    quote_counts = Counter(row[0] for row in db.session.query(Quote.tweet_id).filter(Quote.tweet_id.in_(tweet_ids), Quote.is_removed.is_(False)).all()) if tweet_ids else Counter()
    post_performance = []
    for tweet in sorted(tweets, key=lambda item: item.timestamp, reverse=True):
        reposts = repost_counts[tweet.id]; quotes = quote_counts[tweet.id]; engagements = reposts + quotes
        post_performance.append({'tweet':tweet,'reposts':reposts,'quotes':quotes,'engagements':engagements})
    hashtag_totals = Counter(); hashtag_engagement = Counter()
    for item in post_performance:
        tags = {tag.lower() for tag in HASHTAG_RE.findall(item['tweet'].content or '')}
        for tag in tags:
            hashtag_totals[tag] += 1; hashtag_engagement[tag] += item['engagements']
    hashtag_performance = [{'tag':tag,'posts':count,'engagements':hashtag_engagement[tag]} for tag, count in hashtag_totals.most_common()]
    total_engagements = stats['reposts_received'] + stats['quotes_received']; stats['engagements'] = total_engagements; stats['engagements_per_post'] = round(total_engagements / stats['posts'], 2) if stats['posts'] else 0
    return render_template('creator_analytics.html', stats=stats, post_performance=post_performance, hashtag_performance=hashtag_performance)


@login_required
def edit_profile():
    ripple_plus = current_user.has_entitlement('ripple_plus')
    if request.method == 'POST':
        current_user.username=request.form['username']; current_user.email=request.form['email']; current_user.bio=request.form['bio']
        if ripple_plus:
            requested_theme=(request.form.get('profile_theme') or 'ripple').strip().lower()
            if requested_theme not in PROFILE_THEMES: flash('Choose one of the available Ripple+ profile themes.','danger'); return render_template('edit_profile.html',user=current_user,ripple_plus=True,profile_themes=PROFILE_THEMES)
            current_user.profile_theme=requested_theme
            if request.form.get('remove_banner')=='1': current_user.profile_banner=None
            banner=request.files.get('profile_banner')
            if banner and banner.filename:
                error,banner_name=_store_profile_banner(banner)
                if error: flash(error,'danger'); return render_template('edit_profile.html',user=current_user,ripple_plus=True,profile_themes=PROFILE_THEMES)
                current_user.profile_banner=banner_name
        db.session.commit(); flash('Your profile has been updated!','success'); return redirect(url_for('profile',username=current_user.username))
    return render_template('edit_profile.html',user=current_user,ripple_plus=ripple_plus,profile_themes=PROFILE_THEMES)


@login_required
def followers(username):
    user=User.query.filter_by(username=username).first_or_404(); return render_template('followers.html',user=user,followers=user.followers.all())
@login_required
def following(username):
    user=User.query.filter_by(username=username).first_or_404(); return render_template('following.html',user=user,following=user.followed.all())
@login_required
def unfollow_from_list(user_id):
    user=db.get_or_404(User,user_id)
    if user in current_user.followed: current_user.followed.remove(user); db.session.commit(); snapshot_followers(user); flash(f'You have unfollowed {user.username}.','success')
    return redirect(url_for('following',username=current_user.username))


@profiles_blueprint.record_once
def register_profile_routes(state):
    state.app.add_url_rule('/follow/<username>',endpoint='follow',view_func=follow,methods=['POST']); state.app.add_url_rule('/unfollow/<username>',endpoint='unfollow',view_func=unfollow,methods=['POST']); state.app.add_url_rule('/profile/<username>',endpoint='profile',view_func=profile); state.app.add_url_rule('/analytics',endpoint='analytics',view_func=analytics); state.app.add_url_rule('/creator/analytics',endpoint='creator_analytics',view_func=creator_analytics); state.app.add_url_rule('/profile/edit',endpoint='edit_profile',view_func=edit_profile,methods=['GET','POST']); state.app.add_url_rule('/followers/<username>',endpoint='followers',view_func=followers); state.app.add_url_rule('/following/<username>',endpoint='following',view_func=following); state.app.add_url_rule('/unfollow_from_list/<int:user_id>',endpoint='unfollow_from_list',view_func=unfollow_from_list)
