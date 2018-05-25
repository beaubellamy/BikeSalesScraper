from requests import get
from requests.exceptions import RequestException
from contextlib import closing
from bs4 import BeautifulSoup
import pandas as pd
import unidecode
#import numpy as np
import re
import time

# helpful insight
#https://stackoverflow.com/questions/33718932/missing-data-when-scraping-website-using-loop?utm_medium=organic&utm_source=google_rich_qa&utm_campaign=google_rich_qa
# https://stackoverflow.com/questions/9446387/how-to-retry-urllib2-request-when-fails

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
    time.sleep(5*multiplier)
    headers = {'User-Agent': 'Mozilla/5.0'} # (Windows; U; Windows NT 5.1; en-GB; rv:1.8.1.6) Gecko/20070725 Firefox/2.0.0.6'}
    # Firefox on Windows: Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.8.1.6) Gecko/20070725 Firefox/2.0.0.6
    # Firefox on Mac: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36
    # Chrome on Linux: Mozilla/5.0 (X11; U; Linux i686; en-US) AppleWebKit/534.3 (KHTML, like Gecko) Chrome/6.0.472.63 Safari/534.3
    # IE on Vista: Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1)




    # Get the html from the url
    try:
        with closing(get(url)) as resp:
            content_type = resp.headers['Content-Type'].lower()
            if is_good_response(resp):
                return resp.content
            else:
                # Unable to get the url response
                return None

    except RequestException as e:
        print('Error during requests to {0} : {1}'.format(url, str(e)))
#        ConnectionError(ProtocolError('Connection aborted.', RemoteDisconnected('Remote end closed connection without response',)),)
#        ConnectionError(ProtocolError('Connection aborted.', OSError("(10060, 'WSAETIMEDOUT')",)),)
#        ConnectionResetError(10054, 'An existing connection was forcibly closed by the remote host', None, 10054, None)
       

def getBikeDetails(BikeContent):
    
    content = BeautifulSoup(BikeContent, 'html.parser')

    details = content.findAll("tr")

    bikeDetails = {}

    if (details is not None):
        for i in range(len(details)):
            
            key = details[i].contents[1].text
            value = details[i].contents[3].text

            print ("{0}: {1}".format(key,value))

            # if key = Bike Facts, value = true

            # for numbers; value = re.sub(r'[^\d.]','',value)
            # key = compression, value = value.split(':')[0].split('±')
            # if key = contains('Need')	or 'Bike Payment' or 'Bike Facts' or 'phone'; ignore the feature

            bikeDetails[key] = value

    return bikeDetails



if __name__ == '__main__':
    '''
    Extract data for the sale of motor bikes.
    '''

    baseUrl = 'https://www.bikesales.com.au'
    
    # loop over each page
    index = 0
    pagelimit = 50
    offset = index* pagelimit
    bikeSales = {}
    multiplier = 1

    #roadBikeURL = baseUrl+'road/photots_only/'
    #url = roadBikeURL+extension
    url = baseUrl+'/bikes/?q=Service%3D%5BBikesales%5D'

    #Search page
    content = get_html_content(url)

    # Get a list of all ski resorts (go through each page)
    html = BeautifulSoup(content, 'html.parser')

    BikeList = html.findAll("a", {"class": "item-link-container"})
    # Go to bike URL to get the details

    bikesPerPage = 5 #len(BikeList)
    for loopindex in range(bikesPerPage):
        individualBikeURL = BikeList[loopindex].attrs['href']
        BikeContent = get_html_content(baseUrl+individualBikeURL)
        
        ## occaissionally the connection is lost, so try again.
        while (BikeContent == None):
            multiplier *= 2
            BikeContent = get_html_content(baseUrl+individualBikeURL,multiplier)
        ## Im not sure why the connection is lost, i might be that the site is trying to guard against scraping software.

        ## connection time out error after a few iterations
        bikeDetails = getBikeDetails(BikeContent)

        #getBikeDetails
        #content = BeautifulSoup(BikeContent, 'html.parser')


        #Photos:
        #content.find("a", {"class": "main-image-link"})
        #Multiple list of photos
        #content.find("ul", {"class": "thumbnails jcarousel-list jcarousel-list-horizontal"})

        #details = content.findAll("tr")

        #bikeDetails = {}

        #if (details is not None):
        #    for i in range(len(details)):
            
        #        key = details[i].contents[1].text
        #        value = details[i].contents[3].text

        #        print ("{0}: {1}".format(key,value))
        #        # clean extranious characters from values, eg Price, Odometer, capacity

        #        # if key = Bike Facts, value = true
        #        # if key = compression ratio, clean the value of +- error
        #        # potentially clean extra detail in value.

        #        bikeDetails[key] = value

        #    bikeSales[bikeDetails['Ref Code']] = {**bikeDetails}

        bikeSales[bikeDetails['Ref Code']] = {**bikeDetails}

    df = pd.DataFrame.from_dict(bikeSales, orient='index')
    df.to_csv('bikeSales.csv', index=False)
