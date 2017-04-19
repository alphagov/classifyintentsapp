
# coding: utf-8

#import numpy as np
#import pandas as pd
import re, requests
import time

def random_url(attempts=5):

    '''
    Query https://www.gov.uk/random every five seconds to build a
    list of random gov.uk urls.
    '''
    i = 0
    
    # Assign a fake url first in case of failure

    r = forgery_py.internet.domain_name()

    while i < attempts:
        try:
            r = requests.get('https://gov.uk/random').url
            r = r.replace('https://www.gov.uk', '')
            time.sleep(5)
            break
        except:
           
            i += 1
        
    return(r)

def clean_url(x, UrlModel, query='\/?browse'):

    '''
    Clean the incoming URL according to rules.
    Note that this is applied after the lookup on the gov.uk content API
    '''
    
    # If FCO government/world/country page:
    # Strip back to /government/world and
    # set org to FCO
    
    url = UrlModel()
    url.full_url = x.full_url
    url.page = x.full_url

    if re.search('/government/world', x.full_url):

        url.org0 = 'Foreign & Commonwealth Office'
        url.page = '/government/world'

    # If full_url starts with /guidance or /government:
    # and there is no org (i.e. not the above)
    # Set page to equal full_url                

    elif re.search('\/guidance|\/government', x.full_url):
        if url.org0 is None:
            url.page = x.full_url  
    
    # If page starts with browse:
    # set page to equal /browse/xxx/ 
    
    elif re.search('\/browse', x.full_url):
        url.page = reg_match(query, x.full_url, 1)
              
        # Set section to be /browse/--this-bit--/

        url.section0 = reg_match(query, x.full_url, 2)
            
        # Otherwise:
        # Strip back to the top level
    
    elif ((x.full_url == '/') or re.search('^/search.*', x.full_url) or re.search('^/help.*', x.full_url)):
        url.section0 = 'site-nav'
        url.section1 = 'site-nav'

    elif re.search('^/contact.*', x.full_url):
        url.section0 = 'contact'
        url.section1 = 'contact'

    else:
        url.page = '/' + reg_match('.*', x.full_url, 0)
    
    # If none of the above apply, then simply return the Urls
    # object with the same page

    return(url)

def api_lookup(Raw, Urls):

    '''
    Run a lookup of Raw.full_url against the gov.uk content API
    and store in the Urls table.

    This is run on the 'cleaned' pages which are produced by clean_urls
    '''

    print('***** Running api_lookup() method *****')
    print('*** This may take some time depending on the number of URLS to look up')

    # self.org_sect = [get_org(i) for i in self.data.loc[((self.data.section == 'nan') &(self.data.org == 'nan')),['page']]]
    raw_urls = Raw.query.all()
    
    
    
    [get_org(i) for i in self.unique_pages['page']]
    self.org_sect = pd.DataFrame(self.org_sect, columns=column_names)
    self.org_sect = self.org_sect.set_index(self.unique_pages.index)
 
    # Convert any NaNs to none, so they are not dropped when self.trainer/predictor is run
        
    self.org_sect['organisation0'].replace(np.nan, 'none', regex=True, inplace=True)
    self.org_sect['section0'].replace(np.nan, 'none', regex=True, inplace=True)   

    # Retain the full lookup, but only add a subset of it to the clean dataframe

    org_sect = self.org_sect[['organisation0','section0']]
    org_sect.columns = ['org','section']
 
    self.unique_pages = pd.concat([self.unique_pages, org_sect], axis = 1)
        
    print('*** Lookup complete, merging results back into survey.data')

    self.data = pd.merge(right = self.data.drop(['org','section'], axis=1), left = self.unique_pages, on='page', how='outer')

    self.data.drop_duplicates(subset=['respondent_ID'],inplace=True)
     

def lookup(r, page, index):
    
    '''Helper function to extract results from GOV.UK content api lookup'''

    try:
        if page == 'mainstream_browse_pages':
            x = r['results'][0][page][index]            
        elif page == 'organisations':
            x = r['results'][0][page][index]['title']
        else:
            print('page argument must be one of "organisations" or "mainstream_browse_pages"')
            sys.exit(1)
    except (IndexError, KeyError) as e:
        x = 'null'
    return(x)


def get_org(x):
    
    '''
    Simple function to lookup a url on the GOV.UK content API
    Returns a list.
    '''

    output = []

    # argument x should be pd.Series of full length urls
    # Loop through each entry in the series

    url = "https://www.gov.uk/api/search.json?filter_link[]=%s&fields=organisations&fields=mainstream_browse_pages" % x
    
    #print('Looking up ' + url)
    
    try:
       
        # read JSON result into r
        r = requests.get(url).json()

        # chose the fields you want to scrape. This scrapes the first 5 instances of organisation, error checking as it goes
        # this exception syntax might not work in Python 3

        org0 = lookup(r,'organisations', 0)
        org1 = lookup(r,'organisations', 1)
        org2 = lookup(r,'organisations', 2)
        org3 = lookup(r,'organisations', 3)
        org4 = lookup(r,'organisations', 4)
        section0 = lookup(r,'mainstream_browse_pages', 0)
        section1 = lookup(r,'mainstream_browse_pages', 1)
        section2 = lookup(r,'mainstream_browse_pages', 2)
        section3 = lookup(r,'mainstream_browse_pages', 3)

        output = [
            org0,
            org1,
            org2,
            org3,
            org4,
            section0,
            section1,
            section2,
            section3
            ]
 
        return(output)

    except Exception as e:
        print('Error looking up ' + url)
        print('Returning "null"')
        row = ['null'] * 9
        return(output)


def reg_match(r, x, i):

    '''
    Helper function for dealing with urls beginning /browse/...
    or similar. Utilised in clean_url()
    '''

    r = r + '/'
    
    # r = uncompiled regex query
    # x = string to search
    # i = index of captive group (0 = all)
    
    p = re.compile(r)
    s = p.search(x)
    
    if s:
        t = re.split('\/', x, maxsplit=3)
        if i == 0:
            found = t[1]
        if i == 1:
            found = '/' + t[1] + '/' + t[2]
        elif i == 2:
            found = t[2]
    else: 
        found = x
    return(found)

