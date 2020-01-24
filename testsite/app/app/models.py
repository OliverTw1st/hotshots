from datetime import datetime
from flask import current_app
from time import time
import jwt
from app import db, login
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from hashlib import md5
import uuid

followers = db.Table('followers',
    db.Column('follower_id', db.Integer, db.ForeignKey('user.id')),
    db.Column('followed_id', db.Integer, db.ForeignKey('user.id'))
)

@login.user_loader
def load_user(id):
    return User.query.get(int(id))

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    posts = db.relationship('Post', backref='author', lazy='dynamic')
    telescopes = db.relationship('Telescope', backref='telescope', lazy='dynamic')
    first_name = db.Column(db.String(64))
    last_name = db.Column(db.String(64))
    api_token = db.Column(db.String(32), index=True, default=uuid.uuid4().hex)
    date_created = db.Column(db.DateTime, default=datetime.utcnow())
    last_login = db.Column(db.DateTime, default=datetime.utcnow)
    about_me = db.Column(db.String(140))
    active = db.Column(db.Boolean, default=True)
    followed = db.relationship(
        'User', secondary=followers,
        primaryjoin=(followers.c.follower_id == id),
        secondaryjoin=(followers.c.followed_id == id),
        backref=db.backref('followers', lazy='dynamic'), lazy='dynamic')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def avatar(self, size):
        digest = md5(self.email.lower().encode('utf-8')).hexdigest()
        return 'https://www.gravatar.com/avatar/{}?d=identicon&s={}'.format(
            digest, size)

    def follow(self, user):
        if not self.is_following(user):
            self.followed.append(user)

    def unfollow(self, user):
        if self.is_following(user):
            self.followed.remove(user)

    def is_following(self, user):
        return self.followed.filter(
            followers.c.followed_id == user.id).count() > 0

    def followed_posts(self):
        followed = Post.query.join(
            followers, (followers.c.followed_id == Post.user_id)).filter(
                followers.c.follower_id == self.id)
        own = Post.query.filter_by(user_id=self.id)
        return followed.union(own).order_by(Post.timestamp.desc())

    def __repr__(self):
        return '<User {}>'.format(self.username)

    def get_reset_password_token(self, expires_in=600):
        return jwt.encode(
            {'reset_password': self.id, 'exp': time() + expires_in},
            app.config['SECRET_KEY'], algorithm='HS256').decode('utf-8')

    @staticmethod
    def verify_reset_password_token(token):
        try:
            id = jwt.decode(token, app.config['SECRET_KEY'],
                            algorithms=['HS256'])['reset_password']
        except:
            return
        return User.query.get(id)

class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.String(140))
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    def __repr__(self):
        return '<Post {}>'.format(self.body)

class Telescope(db.Model):
    telescope_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    lat = db.Column(db.Float)
    lon = db.Column(db.Float)
    location_alias = db.Column(db.String(64))
    fov = db.Column(db.Float)
    software = db.Column(db.String(64))
    camera_model = db.Column(db.String(64))
    time_to_nineteen = db.Column(db.Float)
    robotic = db.Column(db.Boolean)
    date_created = db.Column(db.DateTime)
    active = db.Column(db.Boolean, default=True)
    api_token = db.Column(db.String(3), index=True, default=uuid.uuid4().hex)
    def __repr__(self):
        return '<Telescope {}>'.format(self.telescope_id)

class Galaxy(db.Model):
    galaxy_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64))
    ra = db.Column(db.Float)
    de = db.Column(db.Float)
    dist = db.Column(db.Float)
    z = db.Column(db.Float)
    def __repr__(self):
        return '<Galaxy {}>'.format(self.name)

class Event(db.Model):
    event_id = db.Column(db.Integer, primary_key=True)
    gracedb_id = db.Column(db.String(12), unique=True)
    date_created = db.Column(db.DateTime, default=datetime.utcnow)
    link = db.Column(db.String(128))
    dist = db.Column(db.Float)
    dist_err = db.Column(db.Float)
    active = db.Column(db.Boolean, default=True)
    assigned = db.Column(db.Integer, default=0)
    possible = db.Column(db.Integer)

    def __repr__(self):
        return '<Event {}>'.format(self.gracedb_id)

class Match(db.Model):
    match_id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey('event.event_id'), nullable=False)
    telescope_id = db.Column(db.Integer, db.ForeignKey('telescope.telescope_id'), nullable=False)
    galaxy_id = db.Column(db.Integer, db.ForeignKey('galaxy.galaxy_id'), nullable=False)
    date_created = db.Column(db.DateTime, default=datetime.utcnow)
    date_observed = db.Column(db.DateTime)
    date_confirmed = db.Column(db.DateTime)
    source_found = db.Column(db.Boolean, default=False)
    source_ra = db.Column(db.Float)
    source_de = db.Column(db.Float)
    api_token = db.Column(db.String(32), index=True, default=uuid.uuid4().hex)
    sequence = db.Column(db.Integer)

    def __repr__(self):
        return '<Match {}>'.format(self.match_id) 

