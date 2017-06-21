from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Length, Email, Regexp, EqualTo
from wtforms import ValidationError
from ..models import User
import safe

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Length(1, 64),
                                             Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Keep me logged in')
    submit = SubmitField('Log In')

class PasswordStrength(object):
    '''
    Custom password strength validator using safe.
    '''
    def __init__(self, message=None):
        if not message:
            message = 'Your password is too easy to guess. Please try again\
                    with a harder to guess password.'
        self.message = message

    def __call__(self, form, field):
        p = field.data
        strength = safe.check(p)
        if strength.strength not in ['medium', 'strong']:
            raise ValidationError(self.message)

class RegistrationForm(FlaskForm):

    email = StringField(
        'Email address',
        validators=[
            DataRequired(),
            Length(1, 64),
            Email(),
            Regexp(regex = '.*\@digital\.cabinet\-office\.gov\.uk', message='Must be a valid @digital.cabinet-office.gov.uk address')
            
            ]
        )

    username = StringField('Name', validators=[
        DataRequired(), Length(1, 64), Regexp('^[A-Za-z][A-Za-z0-9_.]*$', 0,
                                          'Usernames must have only letters, '
                                          'numbers, dots or underscores')])
    password = PasswordField('Password', validators=[
        DataRequired(), 
        EqualTo('password2', message='Passwords must match.'),
        Length(min=8, message='Password must be at least 8 characters in length.'),
        PasswordStrength()
        ])
    password2 = PasswordField('Confirm password', validators=[DataRequired()])
    submit = SubmitField('Register')
    
    def validate_email(self, field):
        if User.query.filter_by(email=field.data).first():
            raise ValidationError('Email already registered.')

    def validate_username(self, field):
        if User.query.filter_by(username=field.data).first():
            raise ValidationError('Username already in use.')


class ChangePasswordForm(FlaskForm):
    old_password = PasswordField('Old password', validators=[DataRequired()])
    password = PasswordField('New password', validators=[
        DataRequired(), 
        EqualTo('password2', message='Passwords must match.'),
        Length(min=8, message='Password must be at least 8 characters in length.'),
        PasswordStrength()
        ])
    password2 = PasswordField('Confirm new password', validators=[DataRequired()])
    submit = SubmitField('Update Password')


class PasswordResetRequestForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Length(1, 64),
                                             Email()])
    submit = SubmitField('Reset Password')


class PasswordResetForm(FlaskForm):
    email = StringField('Email', validators=[
        DataRequired(), Length(1, 64), Email()])
    password = PasswordField('New Password', validators=[
        DataRequired(), EqualTo('password2', message='Passwords must match'), PasswordStrength()])
    password2 = PasswordField('Confirm password', validators=[DataRequired()])
    submit = SubmitField('Reset Password')

    def validate_email(self, field):
        if User.query.filter_by(email=field.data).first() is None:
            raise ValidationError('Unknown email address.')


class ChangeEmailForm(FlaskForm):
    email = StringField('New Email', validators=[DataRequired(), Length(1, 64),
                                                 Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Update Email Address')

    def validate_email(self, field):
        if User.query.filter_by(email=field.data).first():
            raise ValidationError('Email already registered.')
