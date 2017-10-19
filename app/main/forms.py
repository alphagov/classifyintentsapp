from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, BooleanField, SelectField, SubmitField, RadioField
from wtforms.validators import DataRequired, Length, Email, Regexp, InputRequired
from wtforms import ValidationError
from flask_pagedown.fields import PageDownField
from ..models import Role, User, Codes, ProjectCodes, Classified


class NameForm(FlaskForm):
    name = StringField('What is your name?', validators=[DataRequired()])
    submit = SubmitField('Submit')


class EditProfileForm(FlaskForm):
    name = StringField('Real name', validators=[Length(0, 64)])
    location = StringField('Location', validators=[Length(0, 64)])
    about_me = TextAreaField('About me')
    submit = SubmitField('Submit')


class EditProfileAdminForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Length(1, 64),
                                             Email()])
    username = StringField('Username', validators=[
        DataRequired(), Length(1, 64), Regexp('^[A-Za-z][A-Za-z0-9_.]*$', 0,
                                          'Usernames must have only letters, '
                                          'numbers, dots or underscores')])
    confirmed = BooleanField('Confirmed')
    role = SelectField('Role', coerce=int)
    submit = SubmitField('Submit')

    def __init__(self, user, *args, **kwargs):
        super(EditProfileAdminForm, self).__init__(*args, **kwargs)
        self.role.choices = [(role.id, role.name)
                             for role in Role.query.order_by(Role.name).all()]
        self.user = user

    def validate_email(self, field):
        if field.data != self.user.email and \
                User.query.filter_by(email=field.data).first():
            raise ValidationError('Email already registered.')

    def validate_username(self, field):
        if field.data != self.user.username and \
                User.query.filter_by(username=field.data).first():
            raise ValidationError('Username already in use.')


class ClassifyForm(FlaskForm):
    code = RadioField('code_radio', coerce=int, validators=[InputRequired()])

    # Default the project code to 1, which should correspond to 'none'
    # Better solution would be to determine this dynamically.
    # Using ProjectCode.query.filter_by(project_code='none').first()

    project_code = RadioField(
        'project_code_radio',
        coerce=int, default='0', validators=[InputRequired()])

    PII_boolean = BooleanField('PII_boolean')

    submit = SubmitField('Submit')

    @classmethod
    def codes(cls):
        codes_form = cls()

        # Extract codes from Postgres
        # Where there is not and end date yet

        codes = Codes.query.filter(Codes.end_date.is_(None)).all()
        codes_form.code.choices = [(g.code_id, g.code) for g in codes]

        # Extract project_codes from Postgres
        # Where there is not and end date yet

        project_codes = ProjectCodes.query.filter(
            ProjectCodes.end_date.is_(None)).all()
        codes_form.project_code.choices = [(i.project_code_id, i.project_code) for i in project_codes]

        return(codes_form)
