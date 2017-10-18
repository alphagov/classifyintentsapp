from datetime import datetime
import hashlib
from werkzeug.security import generate_password_hash, check_password_hash
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from markdown import markdown
import bleach
from flask import current_app, request, url_for
from flask_login import UserMixin, AnonymousUserMixin
from app.exceptions import ValidationError
from . import db, login_manager
from random import choice


class Permission:
    CLASSIFY = 0x01
    GAMIFY = 0x02
    ADMINISTER = 0x80


class Role(db.Model):
    '''
    Insert roles into the database
    '''
    __tablename__ = 'roles'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)
    default = db.Column(db.Boolean, default=False, index=True)
    permissions = db.Column(db.Integer)
    users = db.relationship('User', backref='role', lazy='dynamic')

    @staticmethod
    def insert_roles():
        roles = {
            'User': (Permission.CLASSIFY, False),
            'User-Gamify': (Permission.CLASSIFY | Permission.GAMIFY, False),
            'Administrator': (0xff, False)
        }
        for r in roles:
            role = Role.query.filter_by(name=r).first()
            if role is None:
                role = Role(name=r)
            role.permissions = roles[r][0]
            role.default = roles[r][1]
            db.session.add(role)
        db.session.commit()

    def __repr__(self):
        return '<Role %s>' % self.name


class User(UserMixin, db.Model):
    '''A user of this classification webapp (as opposed to a person who filled
    in the survey, who is a 'respondent')
    '''
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(64), unique=True, index=True)
    username = db.Column(db.String(64), index=True)
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'))
    password_hash = db.Column(db.String(128))
    confirmed = db.Column(db.Boolean, default=False)
    name = db.Column(db.String(64))
    location = db.Column(db.String(64))
    about_me = db.Column(db.Text())
    member_since = db.Column(db.DateTime(), default=datetime.utcnow)
    last_seen = db.Column(db.DateTime(), default=datetime.utcnow)
    avatar_hash = db.Column(db.String(32))
    classified = db.relationship('Classified', backref='user_classified', lazy='dynamic')

    @staticmethod
    def generate_fake(count=100):
        from sqlalchemy.exc import IntegrityError
        from random import seed
        import forgery_py

        seed()
        for i in range(count):
            u = User(email=forgery_py.internet.email_address(),
                     username=forgery_py.internet.user_name(True),
                     password=forgery_py.lorem_ipsum.word(),
                     confirmed=True,
                     name=forgery_py.name.full_name(),
                     location=forgery_py.address.city(),
                     about_me=forgery_py.lorem_ipsum.sentence(),
                     member_since=forgery_py.date.date(True))
            db.session.add(u)
            try:
                db.session.commit()
            except IntegrityError:
                db.session.rollback()

    def __init__(self, **kwargs):
        super(User, self).__init__(**kwargs)
        if self.role is None:
            if self.email == current_app.config['FLASKY_ADMIN']:
                self.role = Role.query.filter_by(permissions=0xff).first()
            if self.role is None:
                self.role = Role.query.filter_by(default=True).first()
        if self.email is not None and self.avatar_hash is None:
            self.avatar_hash = hashlib.md5(
                self.email.encode('utf-8')).hexdigest()

    @property
    def password(self):
        raise AttributeError('password is not a readable attribute')

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)

    def generate_confirmation_token(self, expiration=3600):
        s = Serializer(current_app.config['SECRET_KEY'], expiration)
        return s.dumps({'confirm': self.id})

    def confirm(self, token):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except:
            return False
        if data.get('confirm') != self.id:
            return False
        self.confirmed = True
        db.session.add(self)
        return True

    def generate_reset_token(self, expiration=3600):
        s = Serializer(current_app.config['SECRET_KEY'], expiration)
        return s.dumps({'reset': self.id})

    def reset_password(self, token, new_password):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except:
            return False
        if data.get('reset') != self.id:
            return False
        self.password = new_password
        db.session.add(self)
        return True

    def generate_email_change_token(self, new_email, expiration=3600):
        s = Serializer(current_app.config['SECRET_KEY'], expiration)
        return s.dumps({'change_email': self.id, 'new_email': new_email})

    def change_email(self, token):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except:
            return False
        if data.get('change_email') != self.id:
            return False
        new_email = data.get('new_email')
        if new_email is None:
            return False
        if self.query.filter_by(email=new_email).first() is not None:
            return False
        self.email = new_email
        self.avatar_hash = hashlib.md5(
            self.email.encode('utf-8')).hexdigest()
        db.session.add(self)
        return True

    def can(self, permissions):
        return self.role is not None and \
            (self.role.permissions & permissions) == permissions

    def is_administrator(self):
        return self.can(Permission.ADMINISTER)

    def ping(self):
        self.last_seen = datetime.utcnow()
        db.session.add(self)

    def gravatar(self, size=100, default='identicon', rating='g'):
        if request.is_secure:
            url = 'https://secure.gravatar.com/avatar'
        else:
            url = 'http://www.gravatar.com/avatar'
        hash = self.avatar_hash or hashlib.md5(
            self.email.encode('utf-8')).hexdigest()
        return '{url}/{hash}?s={size}&d={default}&r={rating}'.format(
            url=url, hash=hash, size=size, default=default, rating=rating)

    def generate_auth_token(self, expiration):
        s = Serializer(current_app.config['SECRET_KEY'],
                       expires_in=expiration)
        return s.dumps({'id': self.id}).decode('ascii')

    @staticmethod
    def verify_auth_token(token):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except:
            return None
        return User.query.get(data['id'])

    def __repr__(self):
        return '<User %s>' % self.username


class AnonymousUser(AnonymousUserMixin):
    def can(self, permissions):
        return False

    def is_administrator(self):
        return False

login_manager.anonymous_user = AnonymousUser


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class Classified(db.Model):
    '''A user's classification/coding of a survey'''
    __tablename__ = 'classified'
    classified_id = db.Column(db.Integer(), primary_key=True, index=True)
    respondent_id = db.Column(
        db.BigInteger(), db.ForeignKey('raw.respondent_id'), index=True)
    coder_id = db.Column(
        db.Integer(), db.ForeignKey('users.id'), nullable=False, index=True)
    code_id = db.Column(
        db.Integer(), db.ForeignKey('codes.code_id'), nullable=False,
        index=True)
    # see also the backref from Raw
    project_code_id = db.Column(
        db.Integer(), db.ForeignKey('project_codes.project_code_id'),
        index=True)
    pii = db.Column(db.Boolean(), index=True)
    date_coded = db.Column(db.DateTime(), nullable=False)

    @staticmethod
    def generate_fake(count=1000, user_count=1):
        from sqlalchemy.exc import IntegrityError
        from random import seed, randint, sample
        from numpy.random import choice
        import forgery_py
        from datetime import datetime
        from sqlalchemy.sql.expression import func

        seed()

        # Load all users into a list and sample n=user_count users

        user_query = User.query.all()
        u_ids = [i.id for i in user_query]
        u_ids = sample(u_ids, user_count)

        # Load codes and project codes for application to surveys

        codes_query = Codes.query.filter(Codes.end_date is None).all()
        project_codes_query = ProjectCodes.query.filter(
            Codes.end_date is None).all()

        # Convert to lists

        c_ids = [i.code_id for i in codes_query]
        pc_ids = [i.project_code_id for i in project_codes_query]

        # Cycle through each user and classify as a human would

        for j in range(user_count):
            for i in range(int(count/user_count)):

                # Choose from surveys that have not already been classified as
                # either PII, difficult, or already classified well.

                raw_query = Priority.query.filter(
                    Priority.priority < 6).first()
                if raw_query:
                    r_id = raw_query.respondent_id

                    r = Classified(
                        respondent_id=r_id,
                        coder_id=int(choice(u_ids)),
                        code_id=int(choice(c_ids)),
                        project_code_id=int(choice(pc_ids)),
                        pii=choice(a=['Yes', 'No'], p=[0.001, 0.999]),
                        date_coded='{:%Y-%m-%d %H:%M:%S.%f}'.format(
                            datetime.now())
                        )
                else:
                    pass
                    print(
                        'No surveys with the right priority remaining to be'
                        'classified. Try running Raw.generate_fake() to create'
                        ' more fake surveys before re-running '
                        'Classified.generate_fake().')

                db.session.add(r)
                try:
                    db.session.commit()
                except IntegrityError:
                    db.session.rollback()

    def __repr__(self):
        return '<respondent_id %s>' % self.respondent_id


class Raw(db.Model):
    '''Represents a survey (i.e. the thing that gets classified).

    The data is inserted raw from the survey software, so that determines the
    structure.
    '''
    __tablename__ = 'raw'
    respondent_id = db.Column(db.BigInteger(), primary_key=True, index=True)
    collector_id = db.Column(db.String())
    start_date = db.Column(db.DateTime(), index=True)
    end_date = db.Column(db.DateTime(), index=True)
    full_url = db.Column(db.String())
    cat_work_or_personal = db.Column(db.String(20))  # work or personal
    comment_what_work = db.Column(db.String())
    comment_why_you_came = db.Column(db.String())
    cat_found_looking_for = db.Column(db.String(20))
    comment_other_found_what = db.Column(db.String())
    cat_satisfaction = db.Column(db.String(50))
    comment_other_where_for_help = db.Column(db.String())
    cat_anywhere_else_help = db.Column(db.String(30))
    comment_other_else_help = db.Column(db.String())
    comment_where_for_help = db.Column(db.String())
    comment_further_comments = db.Column(db.String())
    classified = db.relationship(
        'Classified', backref='surveys_classified', lazy='dynamic')

    def __repr__(self):
        return '<respondent_id %s start_date %s>' % (
            self.respondent_id, self.start_date)

    @staticmethod
    def get_urls(count=10, file='govukurls.txt'):

        """
        Method to create a list of urls for use in the generate_fake()
        method.
        """

        import re
        import requests
        import forgery_py
        import time
        from app.urllookup import random_url

        # Create a list of 100 urls

        print('Looking up %s random gov.uk pages' % count)
        print('This may take some time...')

        govukurls = [random_url(count) for i in range(count)]

        # Write urls to a file

        with open(file, 'a') as f:
            govukurls = map(lambda x: x+'\n', govukurls)
            f.writelines(govukurls)

        print('...lookup complete')
        print('Appending to %s' % file)

    @staticmethod
    def generate_fake(count=100):
        from sqlalchemy.exc import IntegrityError
        from random import seed, randint, choice
        import forgery_py

        # Load a random list of gov.uk urls

        with open('govukurls.txt') as f:
            govukurls = f.read().splitlines()

        seed()
        for i in range(count):
            r = Raw(
                respondent_id=randint(10000000, 50000000),
                collector_id=999999,
                start_date=forgery_py.date.date(True),
                end_date=forgery_py.date.date(True),
                full_url=choice(govukurls),
                cat_work_or_personal=forgery_py.lorem_ipsum.word(),
                comment_what_work=forgery_py.lorem_ipsum.words(3),
                comment_why_you_came=forgery_py.lorem_ipsum.sentences(2),
                cat_found_looking_for=choice(['Yes','No']),
                comment_other_found_what=forgery_py.lorem_ipsum.sentences(2),
                cat_satisfaction=choice(['Very','Not Very']),
                comment_other_where_for_help=forgery_py.lorem_ipsum.sentences(2),
                cat_anywhere_else_help=choice(['Yes','No']),
                comment_other_else_help=forgery_py.lorem_ipsum.sentence(),
                comment_where_for_help=forgery_py.lorem_ipsum.sentence(),
                comment_further_comments=forgery_py.lorem_ipsum.sentences(3)
            )

            db.session.add(r)
            try:
                db.session.commit()
            except IntegrityError:
                db.session.rollback()

    def __repr__(self):
        return '<respondent_id %s>' % self.respondent_id


class Codes(db.Model):
    '''A classification of the survey comment meaning
    e.g. 'complaint' or 'wanting to contact government'
    '''
    __tablename__ = 'codes'
    code_id = db.Column(db.Integer(), primary_key=True, index=True)
    code = db.Column(db.String(50))
    description = db.Column(db.String())
    start_date = db.Column(db.DateTime())
    end_date = db.Column(db.DateTime())
    classified = db.relationship(
        'Classified', backref='code_surveys', lazy='dynamic')

    def __repr__(self):
        return '<code %s code_id %s>' % (self.code, self.code_id)

    @staticmethod
    def generate_fake(count=10):
        from sqlalchemy.exc import IntegrityError
        from random import seed, randint, choice
        import forgery_py

        seed()

# Add a 'none' class to ensure the default value in the form
# works as expected

        r = Codes(
            code='none',
            description='none',
            start_date=forgery_py.date.date(True),
            end_date=None
            )

        db.session.add(r)
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()

        for i in range(count):
            r = Codes(
                code=forgery_py.lorem_ipsum.word(),
                description=forgery_py.lorem_ipsum.sentence(),
                start_date=forgery_py.date.date(True),
                end_date=choice([None, forgery_py.date.date(True)])
                )

            db.session.add(r)
            try:
                db.session.commit()
            except IntegrityError:
                db.session.rollback()


class ProjectCodes(db.Model):
    '''A classification of the survey comments relationship with a government
    service/project
    e.g. 'GOV.UK Notify'
    '''
    __tablename__ = 'project_codes'
    project_code_id = db.Column(db.Integer(), primary_key=True, index=True)
    project_code = db.Column(db.String(50))
    description = db.Column(db.String())
    start_date = db.Column(db.DateTime())
    end_date = db.Column(db.DateTime())
    classified = db.relationship(
        'Classified', backref='project_surveys', lazy='dynamic')

    def __repr__(self):
        return '<project_code %s project_code_id %s>' % (
            self.project_code, self.project_code_id)

    @staticmethod
    def generate_fake(count=3):
        from sqlalchemy.exc import IntegrityError
        from random import seed, randint, choice
        import forgery_py

        seed()

# Add a 'none' class to ensure the default value in the form
# works as expected

        r = ProjectCodes(
            project_code='none',
            description='none',
            start_date=forgery_py.date.date(True),
            end_date=None
            )

        db.session.add(r)
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()

        for i in range(count):
            r = ProjectCodes(
                project_code=forgery_py.lorem_ipsum.word(),
                description=forgery_py.lorem_ipsum.sentence(),
                start_date=forgery_py.date.date(True),
                end_date=choice([None, forgery_py.date.date(True)])
                )

            db.session.add(r)
            try:
                db.session.commit()
            except IntegrityError:
                db.session.rollback()


class Priority(db.Model):
    '''A calculated 'priority' for each survey, which determines the order that
    users are asked to classify surveys.

    Implemented as a database view.
    '''

    __tablename__ = 'priority'
    respondent_id = db.Column(db.BigInteger(), primary_key=True)
    month = db.Column(db.DateTime())
    max = db.Column(db.BigInteger())
    ratio = db.Column(db.Numeric())
    total = db.Column(db.Integer())
    vote = db.Column(db.Integer())
    coders = db.Column(db.ARRAY(db.Integer()))
    priority = db.Column(db.Integer())

    def __repr__(self):
        return '<respondent_id %s date %s priority %s vote %s>' % (
            self.respondent_id, self.month, self.priority, self.vote)


class Urls(db.Model):
    '''A page on GOV.UK, which is the context for each survey that is filled
    in.
    '''
    __tablename__ = 'urls'
    url_id = db.Column(db.Integer(), primary_key=True, index=True)
    full_url = db.Column(db.String(), index=True)
    page = db.Column(db.String(), index=True)
    org0 = db.Column(db.String(), index=True)
    org1 = db.Column(db.String(), index=True)
    org2 = db.Column(db.String(), index=True)
    org3 = db.Column(db.String(), index=True)
    section0 = db.Column(db.String(), index=True)
    section1 = db.Column(db.String(), index=True)
    section2 = db.Column(db.String(), index=True)
    section3 = db.Column(db.String(), index=True)
    section4 = db.Column(db.String(), index=True)
    section5 = db.Column(db.String(), index=True)
    section6 = db.Column(db.String(), index=True)
    lookup_date = db.Column(db.DateTime(), index=True)
    status = db.Column(db.Integer(), index=True)

    def __repr__(self):
        return '<full_url %s org %s section %s date %s >' % (
            self.full_url, self.org0, self.section0, self.lookup_date)

    @staticmethod
    def bulk_lookup():
        from sqlalchemy.exc import IntegrityError

        # Check to ensure that we haven't already looked up this entry
        # For now, disable this, as it may be necessary to have duplicate
        # full_urls in the Urls table owing to Machinery of Govt changes.

        # urls_full_urls = Urls.query.all()
        # ulrs_full_urls = [i for i in urls_full_urls]

        all_full_urls = Raw.query.filter_by().all()

        r = ProjectCodes(
            project_code='none',
            description='none',
            start_date=forgery_py.date.date(True),
            end_date=None
            )

        db.session.add(r)
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()

        for i in range(count):
            r = ProjectCodes(
                project_code=forgery_py.lorem_ipsum.word(),
                description=forgery_py.lorem_ipsum.sentence(),
                start_date=forgery_py.date.date(True),
                end_date=choice([None, forgery_py.date.date(True)])
                )

            db.session.add(r)
            try:
                db.session.commit()
            except IntegrityError:
                db.session.rollback()


class Leaders(db.Model):
    __tablename__ = 'leaders'
    rank = db.Column(db.Integer(), primary_key=True)
    username = db.Column(db.String(), index=True)
    n = db.Column(db.Integer())


class DailyLeaders(db.Model):
    __tablename__ = 'daily_leaders'
    rank = db.Column(db.Integer(), primary_key=True)
    username = db.Column(db.String(), index=True)
    n = db.Column(db.Integer())


class WeeklyLeaders(db.Model):
    __tablename__ = 'weekly_leaders'
    rank = db.Column(db.Integer(), primary_key=True)
    username = db.Column(db.String(), index=True)
    n = db.Column(db.Integer())
