from flask import render_template, redirect, url_for, abort, flash, request, current_app, make_response
from flask_login import login_required, current_user
from flask_sqlalchemy import get_debug_queries
from . import main
from .forms import EditProfileForm, EditProfileAdminForm, ClassifyForm
from .. import db
from ..models import Permission, Role, User, Classified, Raw, Codes, ProjectCodes, Priority
from ..decorators import admin_required, permission_required
from datetime import datetime, date
from functools import wraps
from random import choice

@main.after_app_request
def after_request(response):
    for query in get_debug_queries():
        if query.duration >= current_app.config['FLASKY_SLOW_DB_QUERY_TIME']:
            current_app.logger.warning(
                'Slow query: %s\nParameters: %s\nDuration: %fs\nContext: %s\n'
                % (query.statement, query.parameters, query.duration,
                   query.context))
    return response


@main.route('/shutdown')
def server_shutdown():
    if not current_app.testing:
        abort(404)
    shutdown = request.environ.get('werkzeug.server.shutdown')
    if not shutdown:
        abort(500)
    shutdown()
    return 'Shutting down...'


def new_survey(user, model):
    '''
    Select the next survey: ensures that a coder doesn't see the same 
    survey more than once.
    
    '''

    # This query can be slow.
    # Filter by 6 will remove all automated and recalcitrant surveys, pii, 
    # And those already happily classified.

    priority = model.query.filter(Priority.priority<6).all()

    priority_list = [i for i in priority if i.coders is None or user not in i.coders]
    
    # Set a limit on how many failures to accept

    count = 0

    while len(priority_list) == 0 and count < 3:

        count += 1

        priority = model.query.filter(Priority.priority<6).all()

        priority_list = [i for i in priority if i.coders is None or user not in i.coders]
    
    return(priority_list)

# Main classification page

@main.route('/', methods=['GET', 'POST'])
@login_required
@permission_required(Permission.CLASSIFY)
def index():

    # Select a survey from the priority view.
    # While loop keeps running until a survey
    # is found that the user has not yet seen.

    priority = new_survey(current_user.id, Priority)    
    
    # Check that there are some entries returned if not
    # Redirect to 'All done page'

    if len(priority) == 0:
        
        flash('You\'re all caught up. Check back later for new surveys.')

        return render_template('404.html')

    else:
        priority = priority[0]
    
        survey = Raw.query.filter(Raw.respondent_id==priority.respondent_id).first()
        survey_id = survey.respondent_id

        # Create forms for entering code and project_code

        codes_form = ClassifyForm.codes()


        if codes_form.validate_on_submit():
            flash('Survey %s classified' % survey_id)

            # Get number of surveys coded today, and print number on every ten

            coded_today = Classified.query.filter(Classified.coder_id == current_user.id).filter(Classified.date_coded > date.today()).count() + 1
        
            if coded_today%10 == 0:
            
                exclaim = ['Well Done!', 'Great!', 'Congratulations!', 'Great Work!', 
                        'Boom!', 'Amazeballs!', 'Amazing!']

                flash('%s You have coded %d surveys today!' % (choice(exclaim), coded_today))

            # Save data into the Classified table

            survey_classification = Classified(
                respondent_id=survey_id,
                code_id=codes_form.code.data,
                project_code_id=codes_form.project_code.data,
                pii=codes_form.PII_boolean.data,
                date_coded='{:%Y-%m-%d %H:%M:%S.%f}'.format(datetime.now()),
                coder_id=current_user.id
                )

            db.session.add(survey_classification)
            db.session.commit()

            # Here the code is reset (probably not required
            # when working fully)

            return redirect(url_for('main.index'))

        return render_template('index.html', form=codes_form, survey=survey)


@main.route('/user/<username>')
@login_required
def user(username):
    user = User.query.filter_by(username=username).first_or_404()
    page = request.args.get('page', 1, type=int)
    return render_template('user.html', user=user)


@main.route('/edit-profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm()
    if form.validate_on_submit():
        current_user.name = form.name.data
        current_user.location = form.location.data
        current_user.about_me = form.about_me.data
        db.session.add(current_user)
        flash('Your profile has been updated.')
        return redirect(url_for('.user', username=current_user.username))
    form.name.data = current_user.name
    form.location.data = current_user.location
    form.about_me.data = current_user.about_me
    return render_template('edit_profile.html', form=form)


@main.route('/edit-profile/<int:id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_profile_admin(id):
    user = User.query.get_or_404(id)
    form = EditProfileAdminForm(user=user)
    if form.validate_on_submit():
        user.email = form.email.data
        user.username = form.username.data
        user.confirmed = form.confirmed.data
        user.role = Role.query.get(form.role.data)
        user.name = form.name.data
        user.location = form.location.data
        user.about_me = form.about_me.data
        db.session.add(user)
        flash('The profile has been updated.')
        return redirect(url_for('.user', username=user.username))
    form.email.data = user.email
    form.username.data = user.username
    form.confirmed.data = user.confirmed
    form.role.data = user.role_id
    form.name.data = user.name
    form.location.data = user.location
    form.about_me.data = user.about_me
    return render_template('edit_profile.html', form=form, user=user)

@main.route('/codes', methods=['GET'])
@login_required
def code_table():
    codes = Codes.query.filter(Codes.end_date == None).all()
    table = [i.__dict__ for i in codes]
    return render_template('codes.html', table=table)
