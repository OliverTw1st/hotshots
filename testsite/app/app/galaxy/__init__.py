from flask import Blueprint

bp = Blueprint('galaxy', __name__)

from app.galaxy import routes
