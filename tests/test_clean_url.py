import unittest
from app import db, create_app
from flask import current_app
from app.urllookup import clean_url
from app.models import Raw, Urls

class TestCleanUrls(unittest.TestCase):

    def setUp(self):

        self.app = create_app('testing')
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

        no_full_url = Raw(respondent_id = 1, full_url = '/')
        govt_world = Raw(respondent_id = 2, full_url = '/government/world/turkey')
        govt_publications = Raw(respondent_id = 3, full_url = '/government/publications/crown-commercial-service-customer-update-september-2016/crown-commercial-service-update-september-2016')
        govt_guidance = Raw(respondent_id = 4, full_url='/guidance/guidance-for-driving-examiners-carrying-out-driving-tests-dt1/05-candidates-with-an-impairment')
        browse = Raw(respondent_id = 5, full_url='/browse/births-deaths-marriages')
        site_nav0 = Raw(respondent_id = 6, full_url='/search/this-is/a-search/url')
        site_nav1 = Raw(respondent_id = 7, full_url='/help/this/is/a/help/url')
        contact = Raw(respondent_id = 8, full_url='/contact/this/is/a/contact/url')
 

        objects = [no_full_url, govt_world, govt_publications,\
                     govt_guidance, browse, site_nav0, site_nav1, contact]
        db.session.bulk_save_objects(objects)
        db.session.commit()        

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    
    def test_clean_url_on_no_full_url(self):
        
        bar = Raw.query.get(1)
        foo = clean_url(bar, Urls)
        self.assertTrue(foo.full_url == bar.full_url)
        self.assertTrue(foo.page == bar.full_url)
        self.assertTrue(foo.section0 == 'site-nav')
        self.assertTrue(foo.section1 == 'site-nav')
        self.assertTrue(foo.org0 is None)
        
    def test_clean_url_on_govt_world(self):

        bar = Raw.query.get(2)
        foo = clean_url(bar, Urls)
        self.assertTrue(foo.full_url == bar.full_url)
        self.assertTrue(foo.page == '/government/world')
        self.assertTrue(foo.section0 is None)
        self.assertTrue(foo.org0 == 'Foreign & Commonwealth Office')

    def test_clean_url_on_govt_publications(self):

        bar = Raw.query.get(3)
        foo = clean_url(bar, Urls)
        self.assertTrue(foo.full_url == bar.full_url)
        self.assertTrue(foo.page == bar.full_url)
        self.assertTrue(foo.section0 is None)
        self.assertTrue(foo.org0 is None)

    def test_clean_url_on_govt_guidance(self):
        bar = Raw.query.get(4)
        foo = clean_url(bar, Urls)
        self.assertTrue(foo.full_url == bar.full_url)
        self.assertTrue(foo.page == bar.full_url)
        self.assertTrue(foo.section0 is None)
        self.assertTrue(foo.org0 is None)


    def test_clean_url_on_browse(self):
        bar = Raw.query.get(5)
        foo = clean_url(bar, Urls)
        self.assertTrue(foo.full_url == bar.full_url)
        self.assertTrue(foo.page == '/browse/births-deaths-marriages')
        self.assertTrue(foo.section0 == 'births-deaths-marriages')
        self.assertTrue(foo.org0 is None)

    def test_clean_url_on_site_nav0(self):
        bar = Raw.query.get(6)
        foo = clean_url(bar, Urls)
        self.assertTrue(foo.full_url == bar.full_url)
        self.assertTrue(foo.page == bar.full_url)
        self.assertTrue(foo.section0 == 'site-nav')
        self.assertTrue(foo.section1 == 'site-nav')
        self.assertTrue(foo.org0 is None)

    def test_clean_url_on_site_nav1(self):
        bar = Raw.query.get(7)
        foo = clean_url(bar, Urls)
        self.assertTrue(foo.full_url == bar.full_url)
        self.assertTrue(foo.page == bar.full_url)
        self.assertTrue(foo.section0 == 'site-nav')
        self.assertTrue(foo.section1 == 'site-nav')
        self.assertTrue(foo.org0 is None)

    def test_clean_url_on_contact(self):
        bar = Raw.query.get(8)
        foo = clean_url(bar, Urls)
        self.assertTrue(foo.full_url == bar.full_url)
        self.assertTrue(foo.page == bar.full_url)
        self.assertTrue(foo.section0 == 'contact')
        self.assertTrue(foo.section1 == 'contact')
        self.assertTrue(foo.org0 is None)
