import re
import unittest
from flask import url_for
from app import create_app, db
from app.models import User, Role
from unittest.mock import patch


class FlaskClientTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app('testing')
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
        Role.insert_roles()
        self.client = self.app.test_client(use_cookies=True)

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

#   Following test will fail in intents app, as anonymous users are
#   not allowed.
#
#    def test_home_page(self):
#        response = self.client.get(url_for('main.index'))
#        self.assertTrue(b'Stranger' in response.data)

    @patch('notifications_python_client.notifications.NotificationsAPIClient.send_email_notification')
    @patch('notifications_python_client.notifications.NotificationsAPIClient.__init__')
    def test_register_and_login(
            self, notify_init, notify_send_email_notification):
        notify_init.return_value = None
        # register a new account
        response = self.client.post(url_for('auth.register'), data={
            'email': 'testemail@digital.cabinet-office.gov.uk',
            'username': 'john',
            'password': 'jhsfaasf7376GHH',
            'password2': 'jhsfaasf7376GHH'
        })
        self.assertTrue(response.status_code == 302)

        # login with the new account
        response = self.client.post(url_for('auth.login'), data={
            'email': 'testemail@digital.cabinet-office.gov.uk',
            'password': 'jhsfaasf7376GHH'
        }, follow_redirects=True)
        self.assertTrue(re.search(b'Hello,\s+john!', response.data))
        self.assertTrue(
            b'You have not confirmed your account yet' in response.data)

        # send a confirmation token
        user = User.query.filter_by(email='testemail@digital.cabinet-office.gov.uk').first()
        token = user.generate_confirmation_token()
        response = self.client.get(url_for('auth.confirm', token=token),
                                   follow_redirects=True)
        self.assertTrue(
            b'You have confirmed your account' in response.data)

        # log out
        response = self.client.get(url_for('auth.logout'), follow_redirects=True)
        self.assertTrue(b'You have been logged out' in response.data)

    def test_register_with_non_gds_email(self):
        # register a new account
        response = self.client.post(url_for('auth.register'), data={
            'email': 'john@anotherdomain.com',
            'username': 'john',
            'password': 'jhsfaasf7376GHH',
            'password2': 'jhsfaasf7376GHH'
        })
        # Response status code will not be 302 (should be 200), as the email
        # address did not validate.
        self.assertTrue(response.status_code != 302)
        self.assertTrue(len(User.query.all()) == 0)
        
