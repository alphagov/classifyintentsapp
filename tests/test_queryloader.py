import unittest
from app import create_app, db
from app.models import User, Role
from app.queryloader import query_loader

class TestQueryLoaderModule(unittest.TestCase):
    def setUp(self):
        self.app = create_app('testing')
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
        Role.insert_roles()
        User.generate_fake(10)
        self.client = self.app.test_client(use_cookies=True)

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_load_and_run_sql_query_from_file(self):

        query = query_loader('tests/example_query.sql')
        result = db.session.execute(query)
        
        self.assertTrue(result.returns_rows)
        self.assertTrue(result.rowcount == 10)

