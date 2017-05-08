import unittest
from app import db, create_app
from flask import current_app
from app.piiremover import pii_remover
from app.models import Raw, Urls

def test_pii_remover_works_with_no_pii(self):

    no_pii = 'This string does not contain pii'   
    self.assertTrue(pii_remover(no_pii) == no_pii)

def test_pii_remover_catches_NI_numbers(self): 
        
    test_cases = ['QQ123456C','QQ 123456 C','QQ 12 34 56 C',
            'QQ123456','QQ 123456','QQ 12 34 56']
        
    success = 'This is not a real national insurance number %s!' % '[PII Removed]'
        
    for i in test_cases:

        feedback = 'This is not a real national insurance number %s!' % i

        self.assertTrue(pii_remover(feedback) == success)           

            
def test_pii_remover_catches_phone_numbers(self): 
        
    '''
    See this link for details on generating fake phone numbers
    https://www.ofcom.org.uk/phones-telecoms-and-internet/
    information-for-industry/numbering/numbers-for-drama
    '''

    test_cases = ['02079461234','0207 946 1234','+442079461234',
        '07700 900123','+447700900123','08081 570123','0909 8790123',
        '(03069) 990123','03069 990123']
    
    success = 'This is not a real telephone number %s!' % '[PII Removed]'
    
    for i in test_cases:

        feedback = 'This is not a real telephone number %s!' % i

        self.assertTrue(pii_remover(feedback) == success)           


def test_pii_remover_catches_credit_card_numbers(self): 
    
    test_cases = ['1234567890123456','1234567890123']
    
    success = 'This is not a real credit card number %s!' % '[PII Removed]'
    
    for i in test_cases:

        feedback = 'This is not a real credit card number %s!' % i

        self.assertTrue(pii_remover(feedback) == success)           

def test_pii_remover_catches_vehicle_reg_plates(self): 
    
    '''
    '''

    test_cases = ['AB12ABC','AB12 ABC']
    
    success = 'This is not a real vehicle registration plate number %s!' % '[PII Removed]'
    
    for i in test_cases:

        feedback = 'This is not a real vehicle registration plate number %s!' % i

        self.assertTrue(pii_remover(feedback) == success)           

class TestPIIRemoval(unittest.TestCase):

    def setUp(self):
        
        self.app = create_app('testing')
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

        comment = 'This is a comment with some pii '
        further_comment = '. And some additional text!'

        national_insurance = Raw(comment_further_comments=comment + 'QQ123456Q' + further_comment)
        phone_number = Raw(comment_further_comments=comment + '02079461234' + further_comment)
        vrp = Raw(comment_further_comments=comment + 'AB12 ABC' + further_comment)
        credit_card = Raw(comment_further_comments=comment + '1234567891234567' + further_comment)
 
        objects = [national_insurance, phone_number, vrp, credit_card]
        db.session.bulk_save_objects(objects)
        db.session.commit()        

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    
    def test_pii_remover_on_database(self):
        
        records = Raw.query.all()
        comments = [pii_remover(i.comment_further_comments) for i in records]
        self.assertTrue(len(set(comments)) == 1)
