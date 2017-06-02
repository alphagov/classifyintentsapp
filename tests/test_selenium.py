import re
import threading
import time
import unittest
from selenium import webdriver
from app import create_app, db
from app.models import Role, User, Raw, Classified, Codes, ProjectCodes
from app.queryloader import query_loader

class SeleniumTestCase(unittest.TestCase):
    client = None
    
    @classmethod
    def setUpClass(cls):
        # start Firefox
        try:
            cls.client = webdriver.Chrome()
        except:
            pass

        # skip these tests if the browser could not be started
        if cls.client:
            # create the application
            cls.app = create_app('testing')
            cls.app_context = cls.app.app_context()
            cls.app_context.push()

            # suppress logging to keep unittest output clean
            import logging
            logger = logging.getLogger('werkzeug')
            logger.setLevel("ERROR")

            # create the database and populate with some fake data
            db.create_all()
            Role.insert_roles()
            User.generate_fake(10)
            Raw.generate_fake(10)
            Codes.generate_fake()
            ProjectCodes.generate_fake()

            # Create the priority view
            db.session.execute('drop table priority, leaders, weekly_leaders, daily_leaders;')
            query = query_loader('sql/views/priority.sql')
            db.session.execute(query)
            query = query_loader('sql/views/leaders.sql')
            db.session.execute(query)
            db.session.commit()
            # add an administrator user
            admin_role = Role.query.filter_by(permissions=0xff).first()
            admin = User(email='john@example.com',
                         username='john', password='cat',
                         role=admin_role, confirmed=True)
            db.session.add(admin)

            # Add a user (without gamification)
            user_role = Role.query.filter_by(name='User').first()
            user = User(email='user@example.com',
                         username='user', password='cat',
                         role=user_role, confirmed=True)
            db.session.add(user)

            db.session.commit()
            # start the Flask server in a thread
            threading.Thread(target=cls.app.run).start()

            # give the server a second to ensure it is up
            time.sleep(1) 

    @classmethod
    def tearDownClass(cls):
        if cls.client:
            # stop the flask server and the browser
            cls.client.get('http://localhost:5000/shutdown')
            cls.client.close()

            # destroy database
            db.session.execute('drop view priority, leaders, weekly_leaders, daily_leaders;')
            db.session.commit()
            db.drop_all()
            db.session.remove()

            # remove application context
            cls.app_context.pop()

    def setUp(self):
        if not self.client:
            self.skipTest('Web browser not available')

    def tearDown(self):
        pass
    
    def test_admin_home_page(self):
        # navigate to home page
        self.client.get('http://localhost:5000/')

        # navigate to login page
        self.client.find_element_by_link_text('Home').click()
        self.assertTrue('<h1>Login</h1>' in self.client.page_source)

        # login
        self.client.find_element_by_name('email').\
            send_keys('john@example.com')
        self.client.find_element_by_name('password').send_keys('cat')
        self.client.find_element_by_name('submit').click()
        #self.assertTrue(re.search('Which\sCODE', self.client.page_source))
    
        # navigate to the user's profile page
        self.client.find_element_by_link_text('Profile').click()
        self.assertTrue('<h1>john</h1>' in self.client.page_source)
        
        # Logout to enable next test
        self.client.find_element_by_link_text('Account').click()
        self.client.find_element_by_link_text('Log Out').click()

    def test_classify_a_survey(self):

        self.client.get('http://localhost:5000/')

        # navigate to login page
        self.client.find_element_by_link_text('Home').click()
        self.assertTrue('<h1>Login</h1>' in self.client.page_source)

        # login
        self.client.find_element_by_name('email').\
            send_keys('user@example.com')
        self.client.find_element_by_name('password').send_keys('cat')
        self.client.find_element_by_name('submit').click()
        #self.assertTrue(re.search('Which\sCODE', self.client.page_source))
    
        # navigate to the user's profile page
        self.client.find_element_by_link_text('Profile').click()
        self.assertTrue('<h1>user</h1>' in self.client.page_source)
        self.client.find_element_by_link_text('Home').click()
        self.client.find_element_by_id('code-0').click()
        self.client.find_element_by_id('project_code-0').click()
        time.sleep(1)
        self.client.find_element_by_name('submit').click()
        
        # Check that a survey was classified     

        classified_count = Classified.query.count()
        self.assertTrue(classified_count == 1)

        # Check that the flashed id corresponds with the survey that was classified

        survey_id = Classified.query.first()
        survey_id = survey_id.respondent_id
        
        flash_id = re.search('Survey\s(\d+)\sclassified', self.client.page_source)
        flash_id = int(flash_id.group(1))
        
        self.assertTrue(survey_id == flash_id)

        # Logout to enable next test
        self.client.find_element_by_link_text('Account').click()
        self.client.find_element_by_link_text('Log Out').click()

