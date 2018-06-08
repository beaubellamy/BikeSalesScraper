from requests import get
from requests.exceptions import RequestException
from contextlib import closing
from bs4 import BeautifulSoup
import pandas as pd
#import unidecode
import numpy as np
import math
#from fractions import Fraction
import re
from datetime import datetime
import time
from random import choice
#import itertools
#import collections.abc
from lxml.html import fromstring
from itertools import cycle
import traceback
#import requests.exceptions
import os
import warnings

# helpful insight
# https://stackoverflow.com/questions/33718932/missing-data-when-scraping-website-using-loop?utm_medium=organic&utm_source=google_rich_qa&utm_campaign=google_rich_qa
# https://stackoverflow.com/questions/9446387/how-to-retry-urllib2-request-when-fails

#HTTPSConnectionPool(host='www.bikesales.com.au', port=443): Max retries exceeded with url: / (Caused by SSLError(SSLError("bad handshake: SysCallError(-1, 'Unexpected EOF')",),))

default_agent = ['Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.99 Safari/537.36']

# Havent confirmed this works yet.
def get_proxies():
    """
    Extract a list of free proxies that can be used avoid the 
    scraper code being detected.
    
    Proxy code from:
    https://www.scrapehero.com/how-to-rotate-proxies-and-ip-addresses-using-python-3/
    """

    url = 'https://free-proxy-list.net/'
    response = get(url)
    parser = fromstring(response.text)
    proxies = set()

    # Configure the proxy list
    for i in parser.xpath('//tbody/tr'):
        if i.xpath('.//td[7][contains(text(),"yes")]'):
            proxy = ":".join([i.xpath('.//td[1]/text()')[0], i.xpath('.//td[2]/text()')[0]])
            proxies.add(proxy)
    return proxies


def get_user_agents():
    """
    Read three files, which contain a list of possible user-agents to assist 
    in avoiding detection of the scraping code.
    """

    with open('Chrome.txt', 'r') as file:
        user_agents = [line.rstrip('\n') for line in file]

    with open('Firefox.txt', 'r') as file:
        user_agents.extend([line.rstrip('\n') for line in file])

    with open('Safari.txt', 'r') as file:
        user_agents.extend([line.rstrip('\n') for line in file])

    # Return the full list of possible user agents
    return user_agents


def is_good_response(resp):
    """
    Ensures that the response is a html object.
    """
    content_type = resp.headers['Content-Type'].lower()
    return (resp.status_code == 200 and 
            content_type is not None 
            and content_type.find('html') > -1)

def get_html_content(url, multiplier=1,user_agents=default_agent,proxy_pool=set()):
    """
    Retrieve the contents of the url, using the proxy and user 
    agent to help avoid scraper detection.
    """
    if not bool(proxy_pool):
        print('There are no proxies in the set list')
        return None

    # Be a responisble scraper.
    # The multiplier is used to exponentially increase the delay when 
    # there are several attempts at connecting to the url
    randomSleep = random.uniform(2,10)  # Randomise the time to sleep to reduce predictability
    time.sleep(randomSleep*multiplier)

    #Choose the next proxy in the list
    proxy = next(proxy_pool)
    
    # Get the html from the url
    try:
        with closing(get(url,
                         headers={'User-Agent': choice(agents).rstrip()},
                         proxies={"http": proxy, "https": proxy})) \
        as resp:
            # Check the response status
            if is_good_response(resp):
                return resp.content
            else:
                # Unable to get the url response
                return None

    except RequestException as e:
        print('Error during requests to {0} : {1}'.format(url, str(e)))
        # Error messages recieved. I should be catching these and properly dealing with them. 
        # I'm not sure how to deal with them properly though.
#        ConnectionError(ProtocolError('Connection aborted.', RemoteDisconnected('Remote end closed connection without response',)),)
#        ConnectionError(ProtocolError('Connection aborted.', OSError("(10060, 'WSAETIMEDOUT')",)),)
#        ConnectionResetError(10054, 'An existing connection was forcibly closed by the remote host', None, 10054, None)
       

def getBikeDetails(BikeContent):
    """
    Search for the relevant Bike information.
    """

    content = BeautifulSoup(BikeContent, 'html.parser')

    # Photos:
    # content.find('a', {'class': 'main-image-link'})
    # Multiple list of photos
    # content.find('ul', {'class': 'thumbnails jcarousel-list jcarousel-list-horizontal'})

    details = content.findAll('tr')

    bikeDetails = {}

    if (details is not None):
        # Loop through all the possible features
        for i in range(len(details)):
            
            # Extract the key and values for each feature.
            key = details[i].contents[1].text
            value = details[i].contents[3].text
            
            # Extract numbers from all features that have one, except:
            leaveAsText = ['Bike', 'Body', 'Configuration', 'Reg Plate', 'Reg Expiry', 'Ref Code', 'Stock Number',
                          'Engine Description', 'Compression Ratio', 'Battery Description', 'Wheel Type',
                          'Wheel Size Front', 'Wheel Size Rear', 'Rear Tyre', 'Front Tyre', 'Seat Description',
                          'Carburettor', 'Exhaust Description', 'Transmission Description', 'Clutch Type',
                          'Chassis Description', 'Front Suspension', 'Rear Suspension', 'Front Brake Description',
                          'Rear Brake Description', 'Instruments / Dash Description', 'Exhaust Config',
                          'Primary Drive', 'Spark Plug Description', 'Ignition Description', 
                          'Economy Mode', 'Weight Distribution Front/Rear']
 
            # Get the numbers out.
            if (re.sub(r'[^\d.]','',value) != '' and key not in leaveAsText):
                value = re.sub(r'[^\d.]','',value)
           
            # Process the drive ratio values
            if (key == 'Final Drive Ratio'):
                if ('/' in value):
                    temp = value.split('/')
                    value = float(temp[0])/float(temp[1])
                elif (':' in value):
                    value = float(value.split(':')[0])
                else:
                    try:
                        value = float(value)
                    except ValueError:
                        continue

            # Process the compression ratio
            if (key == 'Compression Ratio'):
               value = float(value.split(':')[0].split('±')[0])

            # Configure the exhaust configuration and force text interpretation in csv file
            if (key == 'Exhaust Config'):
               value = "'"+re.sub(':','-',value)
            
            # Convert the modified date to a datetime object.
            if (key == 'Last Modified Date'):
                value = datetime.strptime(value,'%d%m%Y')

            # Extract the months left on registration
            if (key == 'Reg Expiry'):
                if ('Month' in value):
                    value = int(value.split('Month')[0])
                elif (value != ''):
                    expiry = datetime.strptime(value, '%B %Y')
                    today = datetime.today()
                    deltaDays = (expiry-today).days
                    if (deltaDays < 0):
                        value = 0
                    else:
                        value = int(math.ceil(deltaDays/30))
                else:
                    continue
    
            # Ignore these features as they dont/wont provide any information
            if ('Need' not in key and key != 'Bike Payment' and key != 'Bike Facts' and key != 'phone'):
                bikeDetails[key] = value


    return bikeDetails

#def request(method, retry=None, *args, **kwargs):
#    if retry is None:
#        retry = iter()
#    elif retry == -1:
#        retry = (2**i for i in itertools.count())
#    elif isinstance(retry, int):
#        retry = (2**i for i in range(retry))
#    elif isinstance(retry, collections.abc.Iterable):
#        pass
#    else:
#        raise ValueError('Unknown retry {retry}'.format(retry=retry))

#    for sleep in itertools.chain([0], retry):
#        if sleep:
#            time.sleep(sleep)
#        try:
#            resp = method(*args, **kwargs)
#            if 200 <= resp.status_code < 300:
#                print ('Success: '+args[0])
#                return resp.content
#        except requests.exceptions.RequestException as e:
#            print('Error during requests to {0} : {1}'.format(args[0], str(e)))
#    return None


#def bike_retrys():
#    for i in range(6):
#        yield 2**i
#    while True:
#        yield 32

#def get_bike(url):
#    multiplier = 1
#    while (BikeContent == None):
#        time.sleep(2*multiplier)
#        try:
#            with closing(get(url)) as resp:
#                content_type = resp.headers['Content-Type'].lower()
#                if 200 <= resp.status_code < 300:
#                    return resp.content
#        except RequestException as e:
#            print('Error during requests to {0} : {1}'.format(url, str(e)))
#        if (multiplier < 16):
#            multiplier *= 2
#    return None

#def get_bike(*args, **kwargs):
#    return request(requests.get, bike_retrys(), *args, **kwargs)

def appendDFToCSV_void(df, csvFilePath, sep=","):
    """
    Append the dataframe to an existing file.
    
    This alllows batch processing of the dataframes and 
    reduces the impact of lost data when there is an error.
    """

    # Check if the file already exists
    if not os.path.isfile(csvFilePath):
        df.to_csv(csvFilePath, mode='a', index=False, sep=sep)

    # Check if the dataframes match before adding to file
    elif len(df.columns) != len(pd.read_csv(csvFilePath, nrows=1, sep=sep).columns):
        df.to_csv(csvFilePath+str(datetime.utcnow().time()), mode='a', index=False, sep=sep)
        warnings.warn('Columns do not match!! Dataframe has ' + str(len(df.columns)) + ' columns. CSV file has ' + str(len(pd.read_csv(csvFilePath, nrows=1, sep=sep).columns)) + ' columns.')
        
    elif not (df.columns == pd.read_csv(csvFilePath, nrows=1, sep=sep).columns).all():
        df.to_csv(csvFilePath+str(datetime.utcnow().time()), mode='a', index=False, sep=sep)
        warnings.warn('Columns and column order of dataframe and csv file do not match!!')
    
    # Append the dataframe to the existing file
    else:
        df.to_csv(csvFilePath, mode='a', index=False, sep=sep, header=False)

if __name__ == '__main__':
    """
    Extract details of motorbikes for sale on bikesales.com
    """

    # Create the list of proxies.
    proxies = get_proxies()
    proxy_pool = cycle(proxies)

    # Create the list of user agents
    agents = get_user_agents()

    # Set the base url and extract basic information required for cycling through the website.
    baseUrl = 'https://www.bikesales.com.au'

    # Get the content of teh first page and extract the number of bikes available.
    content = get_html_content(baseUrl,user_agents=agents,proxy_pool=proxy_pool)
    html = BeautifulSoup(content, 'html.parser')    
    numberOfBikes = html.find('span', {'class': 'home-page__stock-counter__count'}).text
    numberOfBikes = float(re.sub(r'[^\d.]','',numberOfBikes))

    # Set the number of bikes shown on a single page
    pagelimit = 10
    # Calculate the number of pages to cycle through.
    numberOfPages = math.ceil(numberOfBikes/pagelimit)
   
    # Create an empty dictionary for the bike sales data
    bikeSales = {}
        
    # loop over each page
    for page in range(2): #numberOfPages):
        
        # Calcaulte the offset for each page display.
        offset = page* pagelimit
        
        # Add in the extension to generalise the search url
        url = baseUrl+'/bikes/?Q=%28Service%3D%5BBikesales%5D%26%28%28%28%28SiloType%3D%5BBrand%20new%20bikes%20available'+ \
                '%5D%7CSiloType%3D%5BBrand%20new%20bikes%20in%20stock%5D%29%7CSiloType%3D%5BDealer%20used%20bikes'+ \
                '%5D%29%7CSiloType%3D%5BDemo%20%26%20near%20new%20bikes%5D%29%7CSiloType%3D%5BPrivate%20used%20bikes%5D%29%29&'+ \
                'Sort=Premium&Offset='+str(offset)+'&Limit='+str(pagelimit)+'&SearchAction=Pagination'

        # Search the current page and Get a list of all bikes on the current page
        content = get_html_content(url,user_agents=agents,proxy_pool=proxy_pool)
        html = BeautifulSoup(content, 'html.parser')
        BikeList = html.findAll('a', {'class': 'item-link-container'})
        
        # Cycle through the list of bikes on each search page.
        for bike in BikeList:

            # Grab the next proxy in the list
            proxy = next(proxy_pool)

            # Get the URL for each bike.
            individualBikeURL = bike.attrs['href']
            BikeContent = get_html_content(baseUrl+individualBikeURL,user_agents=agents,proxy_pool=proxy_pool)
            
            # Extract the data for each bike into a dictionary
            bikeDetails = getBikeDetails(BikeContent)

            # Create a date for data extraction (In UTC time)
            scrapeDate = datetime.utcnow().date()
        
            # Populate the bike sales details for each bike
            bikeSales[bikeDetails['Ref Code']] = {'URL': baseUrl+individualBikeURL, 
                                                  **bikeDetails, 
                                                  'Scraped date': scrapeDate}

        # Convert the dictionary to a pandas dataframe
        bikeDataFrame = pd.DataFrame.from_dict(bikeSales, orient='index')
    
        # Convert learner approved feature into boolean values
        if ('Learner Approved' in bikeDataFrame):
            bikeDataFrame['Learner Approved'] = [False if pd.isnull(a) else True for a in bikeDataFrame['Learner Approved']]
        else:
            bikeDataFrame['Learner Approved'] = False

        # Create a seller feature, this assumes that if there is a stock number, the seller is a dealer.
        if ('Stock Number' in bikeDataFrame):
            bikeDataFrame['Seller'] = ['Private' if pd.isnull(a) else 'Dealer' for a in bikeDataFrame['Stock Number']]
        else:
            bikeDataFrame['Seller'] = 'Private'

        # Write the dataframe to a csv file.
        #bikeDataFrame.to_csv('bikeSales-'+str(scrapeDate)+'.csv', index=False)
        appendDFToCSV_void(bikeDataFrame, 'bikeSales-'+str(scrapeDate)+'.csv', sep=",")
        # NOT TESTED !!!