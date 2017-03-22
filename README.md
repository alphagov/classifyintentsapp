# Classify intents survey web app

This repository contains the source code examples for my O'Reilly book [Flask Web Development](http://www.flaskbook.com).

The commits and tags in this repository were carefully created to match the sequence in which concepts are presented in the book. Please read the section titled "How to Work with the Example Code" in the book's preface for instructions.

## Environmental variables

It is adviseable to use [autoenv](https://github.com/kennethreitz/autoenv) to manage environmental variables. 

Install with: `pip install autoenv`, and then set all environmental variables in a `.env` files.

```
MAIL_USERNAME=*****
MAIL_PASSWORD=*****
DEV_DATABASE_URL=*****
```

You should also follow 12 factor app principles and set the DATABSE_URL environmental variable dynamically with:

```
DATABASE_URL=$(heroku config:get DATABASE_URL -a classifyintents)
```

See [heroku docs](https://devcenter.heroku.com/articles/connecting-to-heroku-postgres-databases-from-outside-of-heroku) for more details.

## Setting up the app

* Push to github, heroku will detect, and build the app
* run `heroku run python manage.py deploy`

If there are issues, you may need to run:

`heroku run python manage.py db upgrade`

This will bring the database up to date with the latest changes to the models.

You may need to run `heroku run python manape.py migrate`

## Common Problems

The following error `AttributeError: 'NoneType' object has no attribute 'drivername'` indicates that the `DEV_INTENTS_DATABASE_URL` environmental variable has not been set.
