import unittest
#from app import db, create_app
#from flask import current_app
from app.piiremover import pii_remover
#from app.models import Raw, Urls

class TestCleanUrls(unittest.TestCase):

    #def setUp(self):

    #def tearDown(self):
    def test_pii_remover_works_with_no_pii(self):

        no_pii = 'This string does not contain pii'   
        self.assertTrue(pii_remover(no_pii) == no_pii)

    def test_pii_remover_catches_NI_numbers(self): 
        
        test_cases = ['QQ123456C','QQ 123456 C','QQ 12 34 56 C',
            'QQ123456','QQ 123456','QQ 12 34 56']
        
        success = 'This is not a real national insurance number %s!' % '[PII Removed]'
        
        for i in test_cases:

            feedback = 'This is not a real national insurance number %s!' % i

            self.assertTrue(pii_remover(feedback,phone=None) == success)           

            
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

            self.assertTrue(pii_remover(feedback,ni=None) == success)           
