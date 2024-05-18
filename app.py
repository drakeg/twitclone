from flask import Flask, render_template, redirect, url_for, request, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_migrate import Migrate
from flask_wtf import CSRFProtect
import re
from datetime import datetime
import hashlib

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///twitter_clone.db'
app.config['SECRET_KEY'] = 'your_secret_key'

db = SQLAlchemy(app)
migrate = Migrate(app, db)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
csrf = CSRFProtect(app)

def gravatar(email, size=100, default='identicon', rating='g'):
    url = 'https://www.gravatar.com/avatar/'
    hash = hashlib.md5(email.lower().encode('utf-8')).hexdigest()
    return f'{url}{hash}?s={size}&d={default}&r={rating}'

@app.context_processor
def utility_processor():
    return dict(gravatar=gravatar)

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

class Tweet(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String(144), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    user = db.relationship('User', backref=db.backref('tweets', lazy=True))

class Retweet(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    tweet_id = db.Column(db.Integer, db.ForeignKey('tweet.id'), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    user = db.relationship('User', backref=db.backref('retweets', lazy=True))
    tweet = db.relationship('Tweet', backref=db.backref('retweets', lazy=True))

class DirectMessage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String(500), nullable=False)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    receiver_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    sender = db.relationship('User', foreign_keys=[sender_id], backref='sent_messages')
    receiver = db.relationship('User', foreign_keys=[receiver_id], backref='received_messages')

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

@app.route('/')
@login_required
def index():
    tweets = Tweet.query.order_by(Tweet.timestamp.desc()).all()
    retweets = Retweet.query.order_by(Retweet.timestamp.desc()).all()
    return render_template('index.html', tweets=tweets, retweets=retweets, current_user=current_user)

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

@app.route('/tweet', methods=['POST'])
@login_required
def tweet():
    content = request.form['content']
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
                    flash('Your direct message has been sent!', 'success')
                else:
                    flash('User not found.', 'danger')
        else:
            tweet = Tweet(content=content, user_id=current_user.id)
            db.session.add(tweet)
            db.session.commit()
            flash('Your tweet has been posted!', 'success')
    else:
        flash('Tweet content exceeds 144 characters.', 'danger')
    return redirect(url_for('index'))

@app.route('/retweet/<int:tweet_id>', methods=['POST'])
@login_required
def retweet(tweet_id):
    tweet = Tweet.query.get_or_404(tweet_id)
    retweet = Retweet(user_id=current_user.id, tweet_id=tweet.id)
    db.session.add(retweet)
    db.session.commit()
    flash('You have retweeted this tweet!', 'success')
    return redirect(url_for('index'))

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
        return jsonify({'status': 'success', 'message': f'You are now following {username}.'})
    return jsonify({'status': 'error', 'message': 'User not found.'})

@app.route('/unfollow/<username>', methods=['POST'])
@login_required
def unfollow(username):
    user = User.query.filter_by(username=username).first()
    if user:
        current_user.followed.remove(user)
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
    app.run(debug=True, port=8000)