from flask import request
from flask_wtf import FlaskForm
from wtforms import StringField, BooleanField, SubmitField, TextAreaField
from wtforms.validators import ValidationError, DataRequired, Length, NumberRange
from app.models import User

class EditProfileForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    about_me = TextAreaField('About me', validators=[Length(min=0, max=140)])
    submit = SubmitField('Submit')

    def __init__(self, original_username, *args, **kwargs):
        super(EditProfileForm, self).__init__(*args, **kwargs)
        self.original_username = original_username

    def validate_username(self, username):
        if username.data != self.original_username:
            user = User.query.filter_by(username=self.username.data).first()
            if user is not None:
                raise ValidationError('Please use a different username.')

class PostForm(FlaskForm):
    post = TextAreaField('Say something', validators=[
        DataRequired(), Length(min=1, max=140)])
    submit = SubmitField('Submit')

class CreateTelescopeForm(FlaskForm):
    telescope_name = StringField('Telescope Name', validators=[DataRequired()])
    lat = StringField('Latitude', validators=[DataRequired()])
    lon = StringField('Longitude', validators=[DataRequired()])
    camera_model = StringField("Camera Model")
    fov = StringField("Camera FOV (in arcmin)", validators=[DataRequired()])
    time_to_nineteen = StringField("Exposure Time (seconds) for 19th Magnitude", validators=[DataRequired()])
    robotic = BooleanField("Robotic Control")
    software = StringField("Observatory Control Software")
    submit = SubmitField('Submit')
