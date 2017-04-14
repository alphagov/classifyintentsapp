
# coding: utf-8

#import numpy as np
#import pandas as pd
import re, requests
import forgery_py
import time

def random_url():
    attempts = 0

    r = forgery_py.internet.domain_name()
    
    while attempts < 5:
        try:
            r = requests.get('https://gov.uk/random').url
            r = r.replace('https://www.gov.uk', '')
            break
        except:
            attempts += 1
            time.sleep(1)
        
    return(r)


def clean_urls(self):

    print('***** Running clean_urls() method *****')

    # First apply URL filtering rules, and output these cleaned URLs to 
    # a DataFrame called unique_pages.

    # Quick fix here - convert the org and section columns back to strings, they previously
    # were converted to categorical. Need to fix this higher upstream.

    self.data.org = self.data.org.astype('str')
    self.data.section = self.data.section.astype('str')

    query = '\/?browse'

    # Add a blank page column

    self.data['page'] = str()

    if 'full_url' in list(self.data.columns):

        for index, row in self.data.iterrows():
    
            # Deal with cases of no address
                
            if ((row['full_url'] == '/') | (row['full_url'] == np.nan) | (str(row['full_url']) == 'nan')):
        
                continue
    
            # If FCO government/world/country page:
            # Strip back to /government/world and
            # set org to FCO
    
            elif re.search('/government/world', str(row['full_url'])):

                self.data.loc[index,['org','page']] = ['Foreign & Commonwealth Office','/government/world']
        
            # If full_url starts with /guidance or /government:
            # and there is no org (i.e. not the above)
            # Set page to equal full_url                

            elif re.search('\/guidance|\/government', str(row['full_url'])):
                if row['org'] == 'nan':
                    self.data.loc[index,'page'] = row['full_url']  
    
            # If page starts with browse:
            # set page to equal /browse/xxx/ 
    
            elif re.search('\/browse', str(row['full_url'])):
                self.data.loc[index, 'page'] = reg_match(query, row['full_url'], 1)
              
            # If the section is also empty:
            # Set section to be /browse/--this-bit--/

                if row['section'] == 'nan':
                    self.data.loc[index, 'section'] = reg_match(query, row['full_url'], 2)
            
            # Otherwise:
            # Strip back to the top level

            else:
                self.data.loc[index, 'page'] = '/' + reg_match('.*', row['full_url'], 0)

    else:
        print('Full_url column not contained in survey.data object.')
        print('Are you working on a raw data frame? You should be!')
            
        
    # Take only urls where there is no org or section.
        
    self.unique_pages = self.data.loc[(self.data['org'] == 'nan') & (self.data['section'] == 'nan'),'page']
        
    # Convert to a DataFrame to make easier to handle

    self.unique_pages = pd.DataFrame(self.unique_pages, columns = ['page'])
        
    # Drop duplicate pages!

    self.unique_pages = self.unique_pages.drop_duplicates()

    print('*** There are ' + str(len(self.unique_pages['page'])) + ' unique URLs to query. These are stored in survey.unique_pages.')


def api_lookup(self):

    # Run the api lookup, then subset the return (we're not really interested in most of what we get back)
        # then merge this back into self.data, using 'page' as the merge key.

    print('***** Running api_lookup() method *****')
    print('*** This may take some time depending on the number of URLS to look up')

    # This is all a bit messy from the origin function.
    # Would be good to clean this up at some point.
        
    column_names = ['organisation0',
                    'organisation1',
                    'organisation2',
                    'organisation3',
                    'organisation4',
                    'section0',
                    'section1',
                    'section2',
                    'section3']
        
    # Only run the lookup on cases where we have not already set an org and section
                   
    # self.org_sect = [get_org(i) for i in self.data.loc[((self.data.section == 'nan') &(self.data.org == 'nan')),['page']]]
    self.org_sect = [get_org(i) for i in self.unique_pages['page']]
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
     

def string_len(x):
    try:

        x = x.str.strip()
        x = x.str.lower()

        x = x.replace(r'\,\s?\,?$|none\,', 'none', regex=True)
        
        # Convert NaN to 'a'. Then when counted this will
        # be a 1. Whilst not 0, any entry with 1 is virtually
        # meaningless, so 1 is a proxy for 0.
        
        x = pd.Series([len(y) for y in x.fillna('a')])
        # Now normalise the scores
        
        x = (x - x.mean()) / (x.max() - x.min())
               
    except Exception as e:
        print('There was an error converting strings to string length column!')
        print('Original error message:')
        print(repr(e))
    return(x)

def string_capsratio(x):
    try:
        if not pd.isnull(x):
            x = sum([i.isupper() for i in x])/len(x)
        else:
            x = 0

    except Exception as e:
        print('There was an error creating capitals ratio on column: ' + x)
        print('Original error message:')
        print(repr(e))
    return(x)

def string_nexcl(x):
    try:
        if not pd.isnull(x):
            x = sum([i == '!' for i in x]) / len(x)
        else:
            x = 0

    except Exception as e:
        print('There was an error creating n of exclamations on column: ' + x)
        print('Original error message:')
        print(repr(e))
    return(x)
    
def clean_date(x):
    try:
        x = pd.to_datetime(x)
               
    except Exception as e:
        print('There was an error cleaning the StartDate column!')
        print('Original error message:')
        print(repr(e))
    return(x)

def date_features(x):
    try:
        x = pd.to_datetime(x)
        
        X = pd.DataFrame({
                'weekday' : x.dt.weekday,
                'day' : x.dt.day,
                'week' : x.dt.week,
                'month' : x.dt.month,
                'year' : x.dt.year,
             })
        
    except Exception as e:
        print('There was an error creating date feature: ' + x)
        print('Original error message:')
        print(repr(e))
    return(X)

def clean_category(x):
    try:
        
        # May be needed if columns are integer
        x = x.apply(str)
        x = x.str.lower()
        x = x.replace(r'null|\#Value\!', 'none', regex=True)
        x = x.fillna('none')
        x = pd.Series(x)
        x = x.astype('category')
        
    except Exception as e:
        print('There was an error cleaning the', x ,'column.')
        print('Original error message:')
        print(repr(e))
    return(x)

def clean_comment(x):
    try:
        
        x = x.str.strip()
        x = x.str.lower()
        
        # Weirdness with some columns being filled with just a comma.
        # Is this due to improper handling of the csv file somewhere?        
        
        x = x.replace(r'\,\s?\,?$|none\,', 'none', regex=True)
        x = x.fillna('none')
        
    except Exception as e:
        print('There was an error cleaning the', x ,'column.')
        print('Original error message:')
        print(repr(e))
    return(x)
      
def clean_code(x, levels):
    try:

       # If the whole column is not null
       # i.e. we want to train rather than just predict

        if not pd.isnull(x).sum() == len(x):        
            x = x.str.strip()
            x = x.str.lower()
            x = x.replace('\_', '\-', regex=True)
        
            # Rules for fixing random errors.
            # Commented out for now 

            #x = x.replace(r'^k$', 'ok', regex=True)
            #x = x.replace(r'^finding_info$', 'finding_general', regex=True)
            #x = x.replace(r'^none$', np.nan, regex=True)
        
            x[~x.isin(levels)] = np.nan
            x = pd.Series(x)
            x = x.astype('category')
        
    except Exception as e:
        print('There was an error cleaning the', x ,'column.')
        print('Original error message:')
        print(repr(e))
    return(x)

#stops = set(stopwords.words("english"))     # Creating a set of Stopwords
#p_stemmer = PorterStemmer() 
#
#def concat_ngrams(x):
#    #if len(x) > 1 & isinstance(x, list):
#    if isinstance(x, tuple):
#        x = '_'.join(x)
#    return(x)
#
#def cleaner(row):
#    
#    # Function to clean the text data and prep for further analysis
#    text = row.lower()                      # Converts to lower case
#    text = re.sub("[^a-zA-Z]"," ",text)          # Removes punctuation
#    text = text.split()                          # Splits the data into individual words 
#    text = [w for w in text if not w in stops]   # Removes stopwords
#    text = [p_stemmer.stem(i) for i in text]     # Stemming (reducing words to their root)
#    text3 = list(ngrams(text, 2))
#    text2 = list(ngrams(text, 3))
#    text = text + text2 + text3
#    text = list([concat_ngrams(i) for i in text])
#    return(text)  

## Functions dealing with the API lookup

def lookup(r,page,index):        
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
    
    # argument x should be pd.Series of full length urls
    # Loop through each entry in the series

    url = "https://www.gov.uk/api/search.json?filter_link[]=%s&fields=organisations&fields=mainstream_browse_pages" % x
    
    #print('Looking up ' + url)
    
    try:
       
        #url = "https://www.gov.uk/api/search.json?filter_link[]=%s&fields=y" % (x, y)

        # read JSON result into r
        r = requests.get(url).json()

        # chose the fields you want to scrape. This scrapes the first 5 instances of organisation, error checking as it goes
        # this exception syntax might not work in Python 3

        organisation0 = lookup(r,'organisations', 0)
        organisation1 = lookup(r,'organisations', 1)
        organisation2 = lookup(r,'organisations', 2)
        organisation3 = lookup(r,'organisations', 3)
        organisation4 = lookup(r,'organisations', 4)
        section0 = lookup(r,'mainstream_browse_pages', 0)
        section1 = lookup(r,'mainstream_browse_pages', 1)
        section2 = lookup(r,'mainstream_browse_pages', 2)
        section3 = lookup(r,'mainstream_browse_pages', 3)

        row = [organisation0,
                organisation1,
                organisation2,
                organisation3,
                organisation4,
                section0,
                section1,
                section2,
                section3]
        
        return(row)

    except Exception as e:
        print('Error looking up ' + url)
        print('Returning "none"')
        row = ['none'] * 9
        return(row)

## Functions dealing with developing a time difference feature

def normalise(x):
    
    x = (x - np.mean(x)) / np.std(x)
    return(x)

def time_delta(x,y):
    
    # Expects datetime objects

    delta = x - y
    # Required for old versions!
    #delta = np.timedelta64(delta, 's')
    #delta = delta.astype('int')
    delta = delta.astype('timedelta64[s]')
    delta = delta.astype('int')

    # normalise statment moved to method to keep this function simple

    return(delta)

def reg_match(r, x, i):

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

