from app import db
from flask import render_template, flash, redirect, url_for, request, g, \
         jsonify, current_app
from flask_login import current_user, login_required
from app.models import User, Post, Galaxy
from datetime import datetime
from app.galaxy import bp
from werkzeug.utils import secure_filename
import os
import urllib.request

@bp.before_request
def before_request():
    if current_user.is_authenticated:
        current_user.last_active = datetime.utcnow()
        db.session.commit()


@bp.route('/view', methods=['GET'])
def list_galaxies():
    return Galaxy

@bp.route('/view/<galaxy_id>', methods=['GET'])
def list_galaxy(galaxy_id):
    return Galaxy

def explore():
    page = request.args.get('page', 1, type=int)
    posts = Post.query.order_by(Post.timestamp.desc()).paginate(
        page, current_app.config['POSTS_PER_PAGE'], False)
    next_url = url_for('main.explore', page=posts.next_num) \
        if posts.has_next else None
    prev_url = url_for('main.explore', page=posts.prev_num) \
        if posts.has_prev else None
    return render_template("index.html", title='Explore', posts=posts.items,
                          next_url=next_url, prev_url=prev_url)

@bp.route('/user/<username>')
def user(username):
    user = User.query.filter_by(username=username).first_or_404()
    page = request.args.get('page', 1, type=int)
    posts = user.posts.order_by(Post.timestamp.desc()).paginate(
        page, current_app.config['POSTS_PER_PAGE'], False)
    next_url = url_for('main.user', username=user.username,
                       page=posts.next_num) if posts.has_next else None
    prev_url = url_for('main.user', username=user.username,
                       page=posts.prev_num) if posts.has_prev else None
    return render_template('user.html', user=user, posts=posts.items,
                           next_url=next_url, prev_url=prev_url)

