import hashlib
from datetime import datetime
from flask import Flask, render_template, redirect, url_for, request, flash
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_migrate import Migrate

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///twitter_clone.db'
app.config['SECRET_KEY'] = 'your_secret_key'

db = SQLAlchemy(app)
migrate = Migrate(app, db)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

class Follows(db.Model):
    follower_id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True)
    followed_id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True)

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), nullable=False, unique=True)
    email = db.Column(db.String(150), nullable=False, unique=True)
    password = db.Column(db.String(150), nullable=False)
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

def gravatar_url(email, size=30):
    email_hash = hashlib.md5(email.lower().encode('utf-8')).hexdigest()
    return f"https://www.gravatar.com/avatar/{email_hash}?d=identicon&s={size}"

@app.context_processor
def utility_processor():
    return dict(gravatar_url=gravatar_url)

@app.route('/')
@login_required
def index():
    tweets = Tweet.query.order_by(Tweet.timestamp.desc()).all()
    retweets = Retweet.query.order_by(Retweet.timestamp.desc()).all()
    
    timeline = sorted(tweets + retweets, key=lambda x: x.timestamp, reverse=True)
    
    return render_template('index.html', timeline=timeline, current_user=current_user)

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
    mentioned_usernames = re.findall(r'@(\w+)', content)
    
    if mentioned_usernames:
        for username in mentioned_usernames:
            user = User.query.filter_by(username=username).first()
            if user:
                # Strip @username from the content
                dm_content = re.sub(r'@\w+', '', content).strip()
                dm = DirectMessage(content=dm_content, sender_id=current_user.id, receiver_id=user.id)
                db.session.add(dm)
        db.session.commit()
        flash('Your direct message has been sent!', 'success')
    else:
        if len(content) <= 144:
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

@app.route('/follow/<username>')
@login_required
def follow(username):
    user = User.query.filter_by(username=username).first()
    if user:
        current_user.followed.append(user)
        db.session.commit()
        flash(f'You are now following {username}!', 'success')
    else:
        flash('User not found.', 'danger')
    return redirect(url_for('index'))

@app.route('/unfollow/<username>')
@login_required
def unfollow(username):
    user = User.query.filter_by(username=username).first()
    if user:
        current_user.followed.remove(user)
        db.session.commit()
        flash(f'You have unfollowed {username}.', 'success')
    else:
        flash('User not found.', 'danger')
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True, port=8000)