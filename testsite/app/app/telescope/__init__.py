from flask import Blueprint

bp = Blueprint('telescope', __name__)

from app.telescope import routes
