import unittest
from app import db, create_app
from app.urllookup import clean_url
from app.models import Raw, Urls


class TestCleanUrls(unittest.TestCase):

    def setUp(self):

        self.app = create_app('testing')
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

        no_full_url = Raw(respondent_id=1, full_url='/')
        govt_world = Raw(respondent_id=2, full_url='/government/world/turkey')
        govt_publications = Raw(respondent_id=3,
                                full_url='/government/publications/crown-'
                                'commercial-service-customer-update-'
                                'september-2016/crown-commercial-'
                                'service-update-september-2016')
        govt_guidance = Raw(respondent_id=4,
                            full_url='/guidance/guidance-for-driving-examiners-'
                            'carrying-out-driving-tests-dt1/05-candidates-with-'
                            'an-impairment')
        browse = Raw(respondent_id=5, full_url='/browse/births-deaths-marriages')
        site_nav0 = Raw(respondent_id=6, full_url='/search/this-is/a-search/url')
        site_nav1 = Raw(respondent_id=7, full_url='/help/this/is/a/help/url')
        contact = Raw(respondent_id=8, full_url='/contact/this/is/a/contact/url')

        objects = [
            no_full_url, govt_world, govt_publications,
            govt_guidance, browse, site_nav0, site_nav1, contact]
        db.session.bulk_save_objects(objects)
        db.session.commit()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_clean_url_on_no_full_url(self):
        
        query = Raw.query.get(1)
        cleaned_url = clean_url(query, Urls)
        self.assertTrue(cleaned_url.full_url == query.full_url)
        self.assertTrue(cleaned_url.page == query.full_url)
        self.assertTrue(cleaned_url.section0 == 'site-nav')
        self.assertTrue(cleaned_url.section1 == 'site-nav')
        self.assertTrue(cleaned_url.org0 is None)

        query = Raw.query.get(2)
        cleaned_url = clean_url(query, Urls)
        self.assertTrue(cleaned_url.full_url == query.full_url)
        self.assertTrue(cleaned_url.page == '/government/world')
        self.assertTrue(cleaned_url.section0 is None)
        self.assertTrue(cleaned_url.org0 == 'Foreign & Commonwealth Office')

        query = Raw.query.get(3)
        cleaned_url = clean_url(query, Urls)
        self.assertTrue(cleaned_url.full_url == query.full_url)
        self.assertTrue(cleaned_url.page == query.full_url)
        self.assertTrue(cleaned_url.section0 is None)
        self.assertTrue(cleaned_url.org0 is None)

        query = Raw.query.get(4)
        cleaned_url = clean_url(query, Urls)
        self.assertTrue(cleaned_url.full_url == query.full_url)
        self.assertTrue(cleaned_url.page == query.full_url)
        self.assertTrue(cleaned_url.section0 is None)
        self.assertTrue(cleaned_url.org0 is None)

        query = Raw.query.get(5)
        cleaned_url = clean_url(query, Urls)
        self.assertTrue(cleaned_url.full_url == query.full_url)
        self.assertTrue(cleaned_url.page == '/browse/births-deaths-marriages')
        self.assertTrue(cleaned_url.section0 == 'births-deaths-marriages')
        self.assertTrue(cleaned_url.org0 is None)

        query = Raw.query.get(6)
        cleaned_url = clean_url(query, Urls)
        self.assertTrue(cleaned_url.full_url == query.full_url)
        self.assertTrue(cleaned_url.page == query.full_url)
        self.assertTrue(cleaned_url.section0 == 'site-nav')
        self.assertTrue(cleaned_url.section1 == 'site-nav')
        self.assertTrue(cleaned_url.org0 is None)

        query = Raw.query.get(7)
        cleaned_url = clean_url(query, Urls)
        self.assertTrue(cleaned_url.full_url == query.full_url)
        self.assertTrue(cleaned_url.page == query.full_url)
        self.assertTrue(cleaned_url.section0 == 'site-nav')
        self.assertTrue(cleaned_url.section1 == 'site-nav')
        self.assertTrue(cleaned_url.org0 is None)

        query = Raw.query.get(8)
        cleaned_url = clean_url(query, Urls)
        self.assertTrue(cleaned_url.full_url == query.full_url)
        self.assertTrue(cleaned_url.page == query.full_url)
        self.assertTrue(cleaned_url.section0 == 'contact')
        self.assertTrue(cleaned_url.section1 == 'contact')
        self.assertTrue(cleaned_url.org0 is None)
