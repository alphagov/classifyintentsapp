[![Build Status](https://travis-ci.org/ukgovdatascience/classifyintentsapp.svg?branch=master)](https://travis-ci.org/ukgovdatascience/classifyintentsapp)
[![codecov](https://codecov.io/gh/ukgovdatascience/classifyintentsapp/branch/master/graph/badge.svg)](https://codecov.io/gh/ukgovdatascience/classifyintentsapp)

# Classify intents survey web app

This repository contains a Flask app designed to improve the process of classifying surveys received in the GOV.UK intents survey.

The app is hosted at [https://classifyintents.herokuapp.com](https://classifyintents.herokuapp.com)


A blog about the survey is available on [gov.uk](https://gdsdata.blog.gov.uk/2016/12/20/using-machine-learning-to-classify-user-comments-on-gov-uk/), whilst the code is available as a [python package](https://github.com/ukgovdatascience/classifyintents) and [supporting scripts](https://github.com/ukgovdatascience/classifyintentspipe).

The underlying framework of the app is based heavily on the micro blogging site by [Miguel Grinberg](https://github.com/miguelgrinberg/flasky) which features in the O'Reilly book [Flask Web Development](http://www.flaskbook.com).

## Getting started

### Environment variables

It is adviseable to use [autoenv](https://github.com/kennethreitz/autoenv) to manage environmental variables.

Install with: `pip install autoenv`, and then set all environmental variables in a `.env` files.

The following variables should be set in `.env`:

* __MAIL_USERNAME__: Email username used for sending confirmations when signing up.
* __MAIL_PASSWORD__: Password for above email account (probably a gmail account)
* __DEV_DATABASE_URL__: URL of the database used for development
* __TEST_DATABASE_URL__: URL of test database.
* __DATABASE_URL__: URL of production database.
* __SECRET_KEY__: Key for Cross Site Forgery Protection.
* __FLASKY_ADMIN__: Email address for administrator account.

Note that `DATABASE_URL` is subject to change if deployed on heroku, and for this reason should be set dynamically following 12 factor app principles with:

```
DATABASE_URL=$(heroku config:get DATABASE_URL -a classifyintents)
```

See [heroku docs](https://devcenter.heroku.com/articles/connecting-to-heroku-postgres-databases-from-outside-of-heroku) for more details.

Note that you will need to set a postgres URI for the DEV and TEST database even if you don't intent to use them, otherwise this can cause errors during set up.

### Setting up the app to run locally

The dev database is setup/migrated using:

```
python manage.py deploy_local
```

This will run the following deployment tasks:

* Create all the database tables.
* Execute sql scripts to create database views.
* Populate the database with fake data.

Ensure that you have specified your email address in the `FLASKY_ADMIN` environment variable, and then register with the application using the registration page.

```
python manage.py runserver
```

You will automatically be granted administrator rights to the web application.

If you are running the server without first setting up a mail account for handling user registrations, you will need to create a user manually. Open a shell:

```
python manage.py shell
```

Then:

```
from app.models import User, Role
admin_id = Role.query.filter(Role.name=='Administrator').with_entities(Role.id).scalar()
u = User(username='admin', email='admin@admin.com', password='pass', role=Role.query.get(admin_id), confirmed=True)
db.session.add(u)
db.session.commit()
```

### Setting up the app on Heroku/other PaaS

* Set up a heroku pipeline to detect pushes on master to github
* Push to github, heroku will detect, and build the app
* Run `heroku run python manage.py deploy` to run deployment tasks on the server.

Following changes to the database migrations can be made with:

```
python manage.py db migrate
python manage.py db upgrade
```

### Generating dummy data

Dummy data is generated as part of the `python manage.py deploy_local` command, but these methods can be run independent of `python manage.py deploy_local` by runnign `python manage.py populate`, or by opening an app specific shell with `python manage.py shell`, and executing the commands:

```
Role.insert_roles()
Raw.generate_fake()
Codes.generate_fake()
ProjectCodes.generate_fake()
User.generate_fake()
Classified.generate_fake()
```

Each method accepts as its first argument the number of records to create. `Classified.generate_fake()` also accepts a second method which specifies the number or random users over which the specified number of Classified records will be spread.
Note that it is possible to 'run out' of eligible surveys to classify using this method, in which case more fake surveys should be generated with `Raw.generate_fake()`.

### Gotchas

#### Manually creating views

Note that the views: priority, leaders, daily_leaders, and weekly_leaders are not created in the migration script, but instead by running the queries contained in sql/views/priority.sql and sql/views/leaders.sql. This is automatically handled in the `python manage.py deploy` and `python manage.py deploy_local` commands.
This may cause confusion if you create tables using `db.create_all()` from the shell instead of using `python manage.py deploy` (which is the best approach).
From the `python manage.py shell` these queries can be executed with:

```
from app.queryloader import *
query = query_loader('sql/views/priority.sql')
db.session.execute(query)
db.session.commit()
```

Note that `Raw.generate_fake()` will use real GOV.UK urls from the govukurls.txt.
These entries are created by the `Raw.get_urls()` method which queries the [gov.uk/random](https://gov.uk/random) page.
Results are stored in the govukurls.txt file and can be appended to by running the `Raw.get_urls()` method taking the number of new pages to add as the first argument.
Note that this process can be quite slow as a 5 second gap is required between each query, in order to return a unique URL.

### Running a local server

```
python manage.py runserver
```

The local server will be available at <https://127.0.0.1:5000>.

### How new surveys are selected (the priority view)

How surveys should be prioritised to users is controlled by the prioritisation view.
Any view could be created in its place with a new set of criteria as required, but at present the prioritisation works on the basis that at least half of all the people coding a survey need to agree before a code can be set. The prioritisation rules are set below:

|Priority|Conditions|
|---|---|
|1|Any survey for which there is not yet a majority (>=50%) of users assigning a single code, and where <= 5 users have coded the survey|
|2|New surveys that have not been coded|
|3|A survey for which a majority (>=50%) has been found, but <5 people have coded the survey.|
|6|The survey has been automatically been classified by algorithm.|
|7|Survey is recalcitrant: when >5 people have coded the survey and there still is not majority.
|8|Survey contains Personally Identifiable Information (has been tagged as such once or more times)|
|9|There is a majority, and more than 5 people have coded the survey.|

Surveys with priority >=6 are removed from circulation (in the case of 7 and 8: pending further action).

Within the priority codes, surveys are ordered by descending date order, so that the most recent survey will always come up first.

Note that respondent_id is not unique in the priority view.
Under circumstances where there is no discernible majority, i.e. there are two or more votes with a majority < 0.5, both these entries will appear in the priority view.

### Is it tested?

You bet. Tests are in the tests/ folder. Either run `python manage.py test` to execute all, (required for database setup and teardown), or you can run individual tests with `python -m unittest tests/test_lookup.py` (for example).

Tests must be run on a postgres data base, so the `TEST_DATABASE_URL` environmental variable must be set in `.env`.

To complete tests using selenium, you will need to download the [chromedriver](https://chromedriver.storage.googleapis.com) and load it into your path, otherwise these tests will pass without failing.

### Common Problems

The following error `AttributeError: 'NoneType' object has no attribute 'drivername'` indicates that the `DEV_DATABASE_URL` environmental variable has not been set.
