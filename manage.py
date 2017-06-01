#!/usr/bin/env python
import os

if os.path.exists('.env'):
    print('Importing environment from .env...')
    for line in open('.env'):
        var = line.strip().split('=')
        if len(var) == 2:
            os.environ[var[0]] = var[1]

from app import create_app, db
from app.models import User, Role, Permission, Codes, Raw, ProjectCodes, Classified, Priority, Urls
from flask_script import Manager, Shell
from flask_migrate import Migrate, MigrateCommand

app = create_app(os.getenv('FLASK_CONFIG') or 'default')
manager = Manager(app)
migrate = Migrate(app, db)


def make_shell_context():
    return dict(
        app=app,
        db=db,
        User=User,
        Role=Role,
        Permission=Permission,
        Codes=Codes,
        ProjectCodes=ProjectCodes,
        Raw=Raw,
        Classified=Classified,
        Priority=Priority,
        Urls=Urls
        )

manager.add_command("shell", Shell(make_context=make_shell_context))
manager.add_command('db', MigrateCommand)


@manager.command
def test(coverage=False):
    """Run the unit tests."""
    import sys
    import unittest
    tests = unittest.TestLoader().discover('tests')
    result = unittest.TextTestRunner(verbosity=2).run(tests)
    if not result.wasSuccessful():
        sys.exit(1)

@manager.command
def profile(length=25, profile_dir=None):
    """Start the application under the code profiler."""
    from werkzeug.contrib.profiler import ProfilerMiddleware
    app.wsgi_app = ProfilerMiddleware(app.wsgi_app, restrictions=[length],
                                      profile_dir=profile_dir)
    app.run()


@manager.command
def deploy():
    """Run deployment tasks."""
    from flask_migrate import upgrade
    from app.models import Role, User
    from app.queryloader import query_loader
    # migrate database to latest revision
 
    upgrade()

    # create user roles
    Role.insert_roles()

    # Create priority view
    query = query_loader('sql/views/priority.sql')
    db.session.execute(query)

    # Create leaders view
    query = query_loader('sql/views/leaders.sql')
    db.session.execute(query)


@manager.command
def populate():
    """Populate database with fake data."""
    from flask_migrate import upgrade
    from app.models import Role, User, Codes, ProjectCodes, Classified
    # migrate database to latest revision
 
    # create user roles

    Raw.generate_fake(1000)
    Codes.generate_fake()
    ProjectCodes.generate_fake()
    User.generate_fake(10)
    
    Classified.generate_fake(500,10)

if __name__ == '__main__':
    manager.run()
