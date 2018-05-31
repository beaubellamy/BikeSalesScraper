from requests import get
from requests.exceptions import RequestException
from contextlib import closing
from bs4 import BeautifulSoup
import pandas as pd
import unidecode
import numpy as np
import math
from fractions import Fraction
import re
from datetime import datetime
import time
from random import choice
import itertools
import collections.abc

import requests.exceptions


# helpful insight
# https://stackoverflow.com/questions/33718932/missing-data-when-scraping-website-using-loop?utm_medium=organic&utm_source=google_rich_qa&utm_campaign=google_rich_qa
# https://stackoverflow.com/questions/9446387/how-to-retry-urllib2-request-when-fails

desktop_agents = ['Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.99 Safari/537.36',
                      'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.99 Safari/537.36',
                      'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.99 Safari/537.36',
                      'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_1) AppleWebKit/602.2.14 (KHTML, like Gecko) Version/10.0.1 Safari/602.2.14',
                      'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.71 Safari/537.36',
                      'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.98 Safari/537.36',
                      'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.98 Safari/537.36',
                      'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36',
                      'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.71 Safari/537.36',
                      'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.99 Safari/537.36',
                      'Mozilla/5.0 (Windows NT 10.0; WOW64; rv:50.0) Gecko/20100101 Firefox/50.0']
headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36'}
agent = {'User-Agent': choice(desktop_agents)}


def is_good_response(resp):
    """
    Ensures that the response is a html.
    """
    content_type = resp.headers['Content-Type'].lower()
    return (resp.status_code == 200 and 
            content_type is not None 
            and content_type.find('html') > -1)

def get_html_content(url, multiplier=1):
    """
    Retrieve the contents of the url.
    """
    # Be a responisble scraper.
    # The multiplier is used to exponentially increase the delay when there are several attempts at connecting to the url
    time.sleep(2*multiplier)

    
    # Declare the browser that is attempting to access the url.
    #headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36'}
    
    # Get the html from the url
    try:
        #with closing(get(url,{'User-Agent': choice(desktop_agents)})) as resp:
        with closing(get(url,headers=agent)) as resp:
            content_type = resp.headers['Content-Type'].lower()
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
    Search the for the relevant Bike information.
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

def request(method, retry=None, *args, **kwargs):
    if retry is None:
        retry = iter()
    elif retry == -1:
        retry = (2**i for i in itertools.count())
    elif isinstance(retry, int):
        retry = (2**i for i in range(retry))
    elif isinstance(retry, collections.abc.Iterable):
        pass
    else:
        raise ValueError('Unknown retry {retry}'.format(retry=retry))

    for sleep in itertools.chain([0], retry):
        if sleep:
            time.sleep(sleep)
        try:
            resp = method(*args, **kwargs)
            if 200 <= resp.status_code < 300:
                print ('Success: '+args[0])
                return resp.content
        except requests.exceptions.RequestException as e:
            print('Error during requests to {0} : {1}'.format(args[0], str(e)))
    return None


def bike_retrys():
    for i in range(6):
        yield 2**i
    while True:
        yield 32

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

def get_bike(*args, **kwargs):
    return request(requests.get, bike_retrys(), *args, **kwargs)


if __name__ == '__main__':
    """
    Extract data for the sale of motor bikes.
    """

    # Set the base url and extract basic information required for cycling through the website.
    baseUrl = 'https://www.bikesales.com.au'

    content = get_html_content(baseUrl)
    html = BeautifulSoup(content, 'html.parser')    
    numberOfBikes = html.find('span', {'class': 'home-page__stock-counter__count'}).text
    numberOfBikes = float(re.sub(r'[^\d.]','',numberOfBikes))
    # Set the number of bikes shown on a single page
    pagelimit = 100
    # Calculate the number of pages to cycle through.
    numberOfPages = math.ceil(numberOfBikes/pagelimit)
   
    # Create an empty dictionary for the bike sales data
    bikeSales = {}
    
    
    # loop over each page
    for page in range(numberOfPages):
        
        # Calcaulte the offset for each page display.
        offset = page* pagelimit
        
        # Add in the extension to generalise the search url
        url = baseUrl+'/bikes/?Q=%28Service%3D%5BBikesales%5D%26%28%28%28%28SiloType%3D%5BBrand%20new%20bikes%20available'+ \
                '%5D%7CSiloType%3D%5BBrand%20new%20bikes%20in%20stock%5D%29%7CSiloType%3D%5BDealer%20used%20bikes'+ \
                '%5D%29%7CSiloType%3D%5BDemo%20%26%20near%20new%20bikes%5D%29%7CSiloType%3D%5BPrivate%20used%20bikes%5D%29%29&'+ \
                'Sort=Premium&Offset='+str(offset)+'&Limit='+str(pagelimit)+'&SearchAction=Pagination'

        # Search the current page and Get a list of all bikes on the current page
        content = get_html_content(url)
        html = BeautifulSoup(content, 'html.parser')
        BikeList = html.findAll('a', {'class': 'item-link-container'})
        
        # Cycle through the list of bikes on each search page.
        for bike in BikeList:

            # Get the URL for each bike.
            individualBikeURL = bike.attrs['href']
            BikeContent = get_bike(baseUrl+individualBikeURL,headers=agent) #{'User-Agent': choice(desktop_agents)})

            # Reset the miltipler for each new url
            #multiplier = 1
            
            ### occasionally the connection is lost, so try again.
            ### Im not sure why the connection is lost, i might be that the site is trying to guard against scraping software.
            
            ## If initial attempt to connect to the url was unsuccessful, try again with an increasing delay
            #while (BikeContent == None):
            #    # Limit the exponential delay to 16x
            #    if (multiplier < 16):
            #        multiplier *= 2
            #    BikeContent = get_html_content(baseUrl+individualBikeURL,multiplier)
            
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
    bikeDataFrame.to_csv('bikeSales-'+str(scrapeDate)+'.csv', index=False)
