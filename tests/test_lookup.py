
import unittest
from flask import current_app
from app.urllookup import get_org
import requests

class get_orgTestCase(unittest.TestCase):
    def setUp(self):
        example_urls = [
            "/government/organisations/prime-ministers-office-10-downing-street"
        ]   
        self.response = get_org(example_urls[0])

    def test_get_org_returns_list(self):
        self.assertTrue(isinstance(self.response, list))

    def test_get_org_returns_nine_items(self):
        self.assertTrue(len(self.response) == 9)

    def test_get_org_returns_correct_org(self):
        self.assertTrue(self.response[0] == "Prime Minister's Office, 10 Downing Street")
