# Classify intents survey web app

This repository contains a Flask app designed to improve the process of classifying surveys received in the GOV.UK intents survey.

The app is hosted at [https://classifyintents.herokuapp.com](https://classifyintents.herokuapp.com)


A blog about the survey is available on [gov.uk](https://gdsdata.blog.gov.uk/2016/12/20/using-machine-learning-to-classify-user-comments-on-gov-uk/), whilst the code is available as a [python package](https://github.com/ukgovdatascience/classifyintents) and [supporting scripts](https://github.com/ukgovdatascience/classifyintentspipe).

The underlying framework of the app is based heavily on the micro blogging site by [Miguel Grinberg](https://github.com/miguelgrinberg/flasky) which features in the O'Reilly book [Flask Web Development](http://www.flaskbook.com).

## Gettting started

### Environmental variables

It is adviseable to use [autoenv](https://github.com/kennethreitz/autoenv) to manage environmental variables. 

Install with: `pip install autoenv`, and then set all environmental variables in a `.env` files.

The following variables should be set in `.env`:

* __MAIL_USERNAME__: Email username used for sending confirmations when signing up.
* __MAIL_PASSWORD__: Password for above email account (probably a gmail account)
* __DEV_DATABASE_URL__: URL of the database used for development
* __DATABASE_URL__: URL of production database.

Note that `DATABASE_URL` is subject to change if deployed on heroku, and for this reason should be set dynamically following 12 factor app principles with:

```
DATABASE_URL=$(heroku config:get DATABASE_URL -a classifyintents)
```

See [heroku docs](https://devcenter.heroku.com/articles/connecting-to-heroku-postgres-databases-from-outside-of-heroku) for more details.

### Setting up the app

* Set up a heroku pipeline to detect pushes on master to github
* Push to github, heroku will detect, and build the app
* Run `heroku run python manage.py deploy` to run deployment tasks on the server
* If it doesn't already exist, run the `priority.sql` script to create the priority view.

Following changes to the database migrations can be made with:

```
python manage.py db migrate 
python manage.py db upgrade
```

### Common Problems

The following error `AttributeError: 'NoneType' object has no attribute 'drivername'` indicates that the `DEV_DATABASE_URL` environmental variable has not been set.
