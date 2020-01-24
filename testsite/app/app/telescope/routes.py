from app import db
from flask import render_template, flash, redirect, url_for, request, g, \
         jsonify, current_app
from flask_login import current_user, login_required
from app.models import User, Post
from datetime import datetime
from app.telescope import bp
from werkzeug.utils import secure_filename
import os
import urllib.request

ALLOWED_EXTENSIONS = set(['txt', 'fit', 'fits', 'png', 'jpg', 'jpeg'])

def allowed_file(filename):
        return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@bp.before_request
def before_request():
    if current_user.is_authenticated:
        current_user.last_active = datetime.utcnow()
        db.session.commit()


@bp.route('/upload', methods=['POST'])
def upload():
	# check if the post request has the file part
	if 'file' not in request.files:
		resp = jsonify({'message' : 'No file part in the request'})
		resp.status_code = 400
		return resp
	file = request.files['file']
	if file.filename == '':
		resp = jsonify({'message' : 'No file selected for uploading'})
		resp.status_code = 400
		return resp
	if file and allowed_file(file.filename):
		filename = secure_filename(file.filename)
		file.save(os.path.join(current_app.config['UPLOAD_FOLDER'], filename))
		resp = jsonify({'message' : 'File successfully uploaded'})
		resp.status_code = 201
		return resp
	else:
		resp = jsonify({'message' : 'Allowed file types are txt, pdf, png, jpg, jpeg, gif'})
		resp.status_code = 400
		return resp
