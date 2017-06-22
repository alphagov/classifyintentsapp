import unittest
from app import db, create_app
from flask import current_app
from app.models import Raw, Urls
from scrubadub import Scrubber, clean

class TestPIIRemoval(unittest.TestCase):

    def test_clean_works_with_no_pii(self):

        no_pii = 'This string does not contain pii'   
        self.assertEqual(clean(no_pii), no_pii)

class TestPIIRemovalOnDB(unittest.TestCase):

    def setUp(self):
        '''
        Set up app context
        '''
        
        self.app = create_app('testing')
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

        comment = 'This is a comment with some pii '
        further_comment = '. And some additional text!'

        national_insurance = Raw(comment_further_comments=comment + 'AB121314C' + further_comment)
        phone_number = Raw(comment_further_comments=comment + '02079461234' + further_comment)
        vehicle = Raw(comment_further_comments=comment + 'AB12 ABC' + further_comment)
        url = Raw(comment_further_comments=comment + 'https://gov.uk' + further_comment)
 
        objects = [national_insurance, phone_number, vehicle, url]
        db.session.bulk_save_objects(objects)
        db.session.commit()

        self.no_names_scrubber = Scrubber()
        self.no_names_scrubber.remove_detector('name')
        self.no_names_scrubber.remove_detector('url')

        self.no_vehicles_scrubber = Scrubber()
        self.no_vehicles_scrubber.remove_detector('name')
        self.no_vehicles_scrubber.remove_detector('vehicle')
        self.no_vehicles_scrubber.remove_detector('url')
    
    def tearDown(self):
        '''
        Tear down app context
        '''
        
        db.session.remove()
        db.drop_all()
        self.app_context.pop()
    
    def test_clean_on_database(self):
        '''
        Remove pii from records loaded from database
        '''
        records = Raw.query.all()
        comments = [clean(i.comment_further_comments) for i in records]
        self.assertTrue('{{NINO}}' in comments[0])
        self.assertTrue('{{PHONE+PASSPORT}}' in comments[1])
        self.assertTrue('{{VEHICLE+NAME}}' in comments[2])
        self.assertTrue('{{URL}}'  in comments[3])
        
        comments = [self.no_names_scrubber.clean(i.comment_further_comments) for i in records]
        self.assertTrue('{{NINO}}' in comments[0])
        self.assertTrue('{{PHONE+PASSPORT}}' in comments[1])
        self.assertTrue('{{VEHICLE}}' in comments[2])
        self.assertTrue('{{URL}}' not in comments[3])
        
        comments = [self.no_vehicles_scrubber.clean(i.comment_further_comments) for i in records]
        self.assertTrue('{{NINO}}' in comments[0])
        self.assertTrue('{{PHONE+PASSPORT}}' in comments[1])
        self.assertTrue('NAME' not in comments[2])
        self.assertTrue('VEHICLE' not in comments[2])
        self.assertTrue('{{VEHICLE+NAME}}' not in comments[2])
        self.assertTrue('{{URL}}' not in comments[3])
