from PIL import Image
import os
from flask import Flask, render_template, redirect, url_for, request, flash, jsonify, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_migrate import Migrate
from flask_wtf import CSRFProtect
from werkzeug.utils import secure_filename
import re
from datetime import datetime, timedelta
import hashlib
from forms import PollForm
from sqlalchemy import text
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
import atexit

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///twitter_clone.db'
app.config['SECRET_KEY'] = 'your_secret_key'
app.config['UPLOAD_FOLDER'] = 'static/uploads'  # Folder to store uploaded images

db = SQLAlchemy(app)
migrate = Migrate(app, db)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
csrf = CSRFProtect(app)

def post_scheduled_tweets():
    now = datetime.utcnow()
    tweets = Tweet.query.filter(Tweet.scheduled_at <= now, Tweet.timestamp == None).all()
    for tweet in tweets:
        tweet.timestamp = now
        db.session.commit()

scheduler = BackgroundScheduler()
scheduler.start()
scheduler.add_job(
    func=post_scheduled_tweets,
    trigger=IntervalTrigger(seconds=60),  # Check every minute
    id='post_scheduled_tweets',
    name='Post scheduled tweets every minute',
    replace_existing=True)

# Shut down the scheduler when exiting the app
atexit.register(lambda: scheduler.shutdown())

def gravatar(email, size=100, default='identicon', rating='g'):
    url = 'https://www.gravatar.com/avatar/'
    hash = hashlib.md5(email.lower().encode('utf-8')).hexdigest()
    return f'{url}{hash}?s={size}&d={default}&r={rating}'

@app.context_processor
def utility_processor():
    trending_hashtags = get_trending_hashtags()
    newest_users = User.query.order_by(User.id.desc()).limit(5).all()
    return dict(gravatar=gravatar, trending_hashtags=trending_hashtags, newest_users=newest_users)

def get_newest_users(limit=5):
    return User.query.order_by(User.id.desc()).limit(limit).all()

def get_trending_hashtags():
    hashtags = {}
    tweets = Tweet.query.all()
    for tweet in tweets:
        tags = re.findall(r'#(\w+)', tweet.content)
        for tag in tags:
            if tag in hashtags:
                hashtags[tag] += 1
            else:
                hashtags[tag] = 1
    sorted_hashtags = sorted(hashtags.items(), key=lambda x: x[1], reverse=True)
    return [tag for tag, count in sorted_hashtags[:5]]

class Follows(db.Model):
    follower_id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True)
    followed_id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True)

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), nullable=False, unique=True)
    email = db.Column(db.String(150), nullable=False, unique=True)
    password = db.Column(db.String(150), nullable=False)
    bio = db.Column(db.String(300))  # Add a bio field for user profile
    followed = db.relationship('User', secondary='follows', 
                               primaryjoin=(id == Follows.follower_id),
                               secondaryjoin=(id == Follows.followed_id),
                               backref=db.backref('followers', lazy='dynamic'), lazy='dynamic')
    notifications = db.relationship('Notification', backref='user', lazy=True)
    bookmarks = db.relationship('Bookmark', backref='bookmark_user', lazy=True)

class Tweet(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String(144), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    image = db.Column(db.String(100), nullable=True)
    scheduled_at = db.Column(db.DateTime, nullable=True)
    user = db.relationship('User', backref=db.backref('tweets', lazy=True))

class Retweet(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    tweet_id = db.Column(db.Integer, db.ForeignKey('tweet.id'), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    user = db.relationship('User', backref=db.backref('retweets', lazy=True))
    tweet = db.relationship('Tweet', backref=db.backref('retweets', lazy=True))

class Quote(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    tweet_id = db.Column(db.Integer, db.ForeignKey('tweet.id'), nullable=False)
    content = db.Column(db.String(144), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    user = db.relationship('User', backref=db.backref('quotes', lazy=True))
    tweet = db.relationship('Tweet', backref=db.backref('quotes', lazy=True))

class DirectMessage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String(500), nullable=False)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    receiver_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    sender = db.relationship('User', foreign_keys=[sender_id], backref='sent_messages')
    receiver = db.relationship('User', foreign_keys=[receiver_id], backref='received_messages')

class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    message = db.Column(db.String(200), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    read = db.Column(db.Boolean, default=False)

class Bookmark(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    tweet_id = db.Column(db.Integer, db.ForeignKey('tweet.id'), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    user = db.relationship('User', backref='bookmark_relationships')
    tweet = db.relationship('Tweet', backref='bookmarked_tweets')

class Poll(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    question = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    duration_days = db.Column(db.Integer, nullable=False)
    duration_hours = db.Column(db.Integer, nullable=False)
    duration_minutes = db.Column(db.Integer, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user = db.relationship('User', backref=db.backref('polls', lazy=True))
    options = db.relationship('PollOption', backref='poll', lazy=True)

    @property
    def is_active(self):
        expiration_time = self.created_at + timedelta(days=self.duration_days, hours=self.duration_hours, minutes=self.duration_minutes)
        return datetime.utcnow() < expiration_time

class PollOption(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    option_text = db.Column(db.String(255), nullable=False)
    poll_id = db.Column(db.Integer, db.ForeignKey('poll.id'), nullable=False)
    votes = db.Column(db.Integer, default=0)

class PollVote(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    poll_id = db.Column(db.Integer, db.ForeignKey('poll.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    option_id = db.Column(db.Integer, db.ForeignKey('poll_option.id'), nullable=False)

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

@app.route('/')
def index():
    now = datetime.utcnow()
    current_time = now.strftime("%Y-%m-%d %H:%M:%S")

    tweets = db.session.query(
        Tweet.id.label('id'), 
        Tweet.content.label('content'), 
        Tweet.timestamp.label('timestamp'), 
        Tweet.user_id.label('user_id'),
        db.literal(None).label('poll_id'),
        db.literal('tweet').label('type')
    ).filter((Tweet.scheduled_at == None) | (Tweet.scheduled_at <= now))

    retweets = db.session.query(
        Retweet.id.label('id'), 
        Retweet.tweet_id.label('content'), 
        Retweet.timestamp.label('timestamp'), 
        Retweet.user_id.label('user_id'),
        db.literal(None).label('poll_id'),
        db.literal('retweet').label('type')
    )

    polls = db.session.query(
        Poll.id.label('id'),
        Poll.question.label('content'),
        Poll.created_at.label('timestamp'),
        Poll.user_id.label('user_id'),
        Poll.id.label('poll_id'),
        db.literal('poll').label('type')
    )

    combined_query = tweets.union_all(retweets, polls).order_by(text('timestamp desc'))

    posts = combined_query.all()

    # Fetch user data and combine with posts
    user_ids = {post.user_id for post in posts}
    users = {user.id: user for user in User.query.filter(User.id.in_(user_ids)).all()}

    posts_with_users = []
    for post in posts:
        post_dict = {
            'id': post.id,
            'content': post.content,
            'timestamp': post.timestamp,
            'user_id': post.user_id,
            'poll_id': post.poll_id,
            'type': post.type,
            'user': users[post.user_id]
        }
        if post.type == 'poll':
            poll = Poll.query.get(post.poll_id)
            post_dict['poll'] = poll
            # Check if the current user has already voted
            if current_user.is_authenticated:
                vote = PollVote.query.filter_by(poll_id=post.poll_id, user_id=current_user.id).first()
                post_dict['has_voted'] = vote is not None
            else:
                post_dict['has_voted'] = False
        posts_with_users.append(post_dict)
    
    trending_hashtags = get_trending_hashtags()  # Assuming this function is defined elsewhere
    newest_users = get_newest_users()  # Assuming this function is defined elsewhere

    return render_template('index.html', posts=posts_with_users, current_time=current_time, trending_hashtags=trending_hashtags, newest_users=newest_users)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        user = User(username=username, email=email, password=hashed_password)
        db.session.add(user)
        db.session.commit()
        flash('Your account has been created!', 'success')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email).first()
        if user and bcrypt.check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('index'))
        else:
            flash('Login Unsuccessful. Please check email and password', 'danger')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

def resize_image(image_path, output_path, size=(200, 200)):
    with Image.open(image_path) as img:
        img.thumbnail(size)
        img.save(output_path)

@app.route('/tweet', methods=['POST'])
@login_required
def tweet():
    content = request.form['content']
    image = request.files.get('image')
    image_filename = None

    if image:
        image_filename = secure_filename(image.filename)
        image_path = os.path.join(app.config['UPLOAD_FOLDER'], image_filename)
        image.save(image_path)
        resized_image_path = os.path.join(app.config['UPLOAD_FOLDER'], f"thumb_{image_filename}")
        resize_image(image_path, resized_image_path)
        image_filename = f"thumb_{image_filename}"

    scheduled_date = request.form.get('scheduled_date')
    scheduled_time = request.form.get('scheduled_time')
    scheduled_at = None
    if scheduled_date and scheduled_time:
        scheduled_at = datetime.strptime(f"{scheduled_date} {scheduled_time}", "%Y-%m-%d %H:%M")

    if len(content) <= 144:
        if content.startswith('/dm '):
            dm_parts = content.split(' ', 2)
            if len(dm_parts) == 3:
                username = dm_parts[1]
                message = dm_parts[2]
                user = User.query.filter_by(username=username).first()
                if user:
                    dm = DirectMessage(content=message, sender_id=current_user.id, receiver_id=user.id)
                    db.session.add(dm)
                    db.session.commit()
                    # Create notification for the receiver
                    notification = Notification(user_id=user.id, message=f'{current_user.username} sent you a message')
                    db.session.add(notification)
                    db.session.commit()
                    flash('Your direct message has been sent!', 'success')
                else:
                    flash('User not found.', 'danger')
        else:
            tweet = Tweet(content=content, user_id=current_user.id, image=image_filename, scheduled_at=scheduled_at)
            db.session.add(tweet)
            db.session.commit()
            if scheduled_at:
                flash('Your tweet has been scheduled!', 'success')
            else:
                flash('Your tweet has been posted!', 'success')
    else:
        flash('Tweet content exceeds 144 characters.', 'danger')
    return redirect(url_for('index'))

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/retweet/<int:tweet_id>', methods=['POST'])
@login_required
def retweet(tweet_id):
    tweet = Tweet.query.get_or_404(tweet_id)
    retweet = Retweet(user_id=current_user.id, tweet_id=tweet.id)
    db.session.add(retweet)
    db.session.commit()
    flash('You have retweeted this tweet!', 'success')
    return redirect(url_for('index'))

@app.route('/quote/<int:tweet_id>', methods=['GET', 'POST'])
@login_required
def quote(tweet_id):
    tweet = Tweet.query.get_or_404(tweet_id)
    if request.method == 'POST':
        content = request.form['content']
        if len(content) <= 144:
            quote = Quote(user_id=current_user.id, tweet_id=tweet.id, content=content)
            db.session.add(quote)
            db.session.commit()
            flash('You have quoted this tweet!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Quote content exceeds 144 characters.', 'danger')
    return render_template('quote.html', tweet=tweet)

@app.route('/messages')
@login_required
def messages():
    messages = DirectMessage.query.filter_by(receiver_id=current_user.id).order_by(DirectMessage.timestamp.desc()).all()
    return render_template('messages.html', messages=messages)

@app.route('/reply/<int:message_id>', methods=['GET', 'POST'])
@login_required
def reply_message(message_id):
    message = DirectMessage.query.get_or_404(message_id)
    if request.method == 'POST':
        content = request.form['content']
        if len(content) <= 500:
            dm = DirectMessage(content=content, sender_id=current_user.id, receiver_id=message.sender_id)
            db.session.add(dm)
            db.session.commit()
            # Create notification for the receiver
            notification = Notification(user_id=message.sender_id, message=f'{current_user.username} replied to your message')
            db.session.add(notification)
            db.session.commit()
            flash('Your reply has been sent!', 'success')
        else:
            flash('Message content exceeds 500 characters.', 'danger')
        return redirect(url_for('messages'))
    
    return render_template('reply.html', message=message)

@app.route('/follow/<username>', methods=['POST'])
@login_required
def follow(username):
    user = User.query.filter_by(username=username).first()
    if user:
        current_user.followed.append(user)
        db.session.commit()
        # Create notification for the followed user
        notification = Notification(user_id=user.id, message=f'{current_user.username} followed you')
        db.session.add(notification)
        db.session.commit()
        return jsonify({'status': 'success', 'message': f'You are now following {username}.'})
    return jsonify({'status': 'error', 'message': 'User not found.'})

@app.route('/unfollow/<username>', methods=['POST'])
@login_required
def unfollow(username):
    user = User.query.filter_by(username=username).first()
    if user:
        current_user.followed.remove(user)
        db.session.commit()
        # Create notification for the unfollowed user
        notification = Notification(user_id=user.id, message=f'{current_user.username} unfollowed you')
        db.session.add(notification)
        db.session.commit()
        return jsonify({'status': 'success', 'message': f'You have unfollowed {username}.'})
    return jsonify({'status': 'error', 'message': 'User not found.'})

@app.route('/profile/<username>')
@login_required
def profile(username):
    user = User.query.filter_by(username=username).first_or_404()
    is_following = user in current_user.followed
    return render_template('profile.html', user=user, is_following=is_following)

@app.route('/profile/edit', methods=['GET', 'POST'])
@login_required
def edit_profile():
    if request.method == 'POST':
        current_user.username = request.form['username']
        current_user.email = request.form['email']
        current_user.bio = request.form['bio']
        db.session.commit()
        flash('Your profile has been updated!', 'success')
        return redirect(url_for('profile', username=current_user.username))
    return render_template('edit_profile.html', user=current_user)

@app.route('/followers/<username>')
@login_required
def followers(username):
    user = User.query.filter_by(username=username).first_or_404()
    followers = user.followers.all()
    return render_template('followers.html', user=user, followers=followers)

@app.route('/following/<username>')
@login_required
def following(username):
    user = User.query.filter_by(username=username).first_or_404()
    following = user.followed.all()
    return render_template('following.html', user=user, following=following)

@app.route('/unfollow_from_list/<int:user_id>')
@login_required
def unfollow_from_list(user_id):
    user = User.query.get_or_404(user_id)
    if user in current_user.followed:
        current_user.followed.remove(user)
        db.session.commit()
        flash(f'You have unfollowed {user.username}.', 'success')
    return redirect(url_for('following', username=current_user.username))

@app.route('/search', methods=['GET', 'POST'])
@login_required
def search():
    if request.method == 'POST':
        search_query = request.form['search_query']
        user_results = User.query.filter(User.username.ilike(f'%{search_query}%')).all()
        tweet_results = Tweet.query.filter(Tweet.content.ilike(f'%#{search_query}%')).all()
        return render_template('search_results.html', search_query=search_query, user_results=user_results, tweet_results=tweet_results)
    return redirect(url_for('index'))

@app.route('/hashtag/<hashtag>')
@login_required
def hashtag(hashtag):
    hashtag = f'#{hashtag}'
    tweets = Tweet.query.filter(Tweet.content.like(f'%{hashtag}%')).order_by(Tweet.timestamp.desc()).all()
    return render_template('hashtag.html', hashtag=hashtag, tweets=tweets)

@app.route('/notifications')
@login_required
def notifications():
    notifications = Notification.query.filter_by(user_id=current_user.id).order_by(Notification.timestamp.desc()).all()
    return render_template('notifications.html', notifications=notifications)

@app.route('/bookmark/<int:tweet_id>', methods=['POST'])
@login_required
def bookmark(tweet_id):
    tweet = Tweet.query.get_or_404(tweet_id)
    bookmark = Bookmark(user_id=current_user.id, tweet_id=tweet.id)
    db.session.add(bookmark)
    db.session.commit()
    flash('Tweet has been bookmarked!', 'success')
    return redirect(url_for('index'))

@app.route('/bookmarks')
@login_required
def bookmarks():
    bookmarks = Bookmark.query.filter_by(user_id=current_user.id).order_by(Bookmark.timestamp.desc()).all()
    return render_template('bookmarks.html', bookmarks=bookmarks)

@app.route('/create_poll', methods=['GET', 'POST'])
@login_required
def create_poll():
    form = PollForm()
    if form.validate_on_submit():
        poll = Poll(
            question=form.question.data,
            duration_days=form.duration_days.data,
            duration_hours=form.duration_hours.data,
            duration_minutes=form.duration_minutes.data,
            user_id=current_user.id
        )
        db.session.add(poll)
        db.session.commit()

        for option in form.options.data:
            poll_option = PollOption(option_text=option['option_text'], poll_id=poll.id)
            db.session.add(poll_option)
        db.session.commit()

        flash('Poll created successfully!', 'success')
        return redirect(url_for('index'))
    
    return render_template('create_poll.html', form=form)

@app.route('/vote_poll/<int:poll_id>', methods=['POST'])
@login_required
def vote_poll(poll_id):
    option_id = request.form.get('option_id')
    if not option_id:
        flash('You must select an option to vote', 'warning')
        return redirect(url_for('index'))

    poll = Poll.query.get_or_404(poll_id)
    option = PollOption.query.get_or_404(option_id)

    # Check if the user has already voted
    vote = PollVote.query.filter_by(poll_id=poll_id, user_id=current_user.id).first()
    if vote:
        flash('You have already voted in this poll', 'warning')
    else:
        new_vote = PollVote(poll_id=poll_id, user_id=current_user.id, option_id=option_id)
        option.votes += 1
        db.session.add(new_vote)
        db.session.commit()
        flash('Your vote has been recorded', 'success')

    return redirect(url_for('index'))

def make_clickable_links(text):
    # Convert @username to clickable links
    text = re.sub(r'@(\w+)', r'<a href="/profile/\1">@\1</a>', text)
    # Convert #hashtag to clickable links
    text = re.sub(r'#(\w+)', r'<a href="/hashtag/\1">#\1</a>', text)
    return text

@app.template_filter('make_clickable')
def make_clickable_filter(text):
    return make_clickable_links(text)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, port=8000)