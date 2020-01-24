import os
basedir = os.path.abspath(os.path.dirname(__file__))

class Config(object):
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'you-will-never-guess'
    
    SQLALCHEMY_DATABASE_URI = "mysql://"+os.environ.get('MYSQL_USER')+":"+os.environ.get('MYSQL_PASSWORD')+"@"+os.environ.get('MYSQL_HOST')+":"+os.environ.get('MYSQL_PORT')+"/"+os.environ.get('MYSQL_DB') or \
    'sqlite:///' + os.path.join(basedir, 'app.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    MAIL_SERVER = os.environ.get('MAIL_SERVER')
    MAIL_PORT = int(os.environ.get('MAIL_PORT') or 25)
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS') is not None
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_FROM = os.environ.get('MAIL_FROM')
    ADMINS = ['chris@iapcrepair.com']
    POSTS_PER_PAGE = 3
    UPLOAD_FOLDER = '/app/app/static'
    MAX_CONTENT_LENGTH = 16 * 1024 *1024
