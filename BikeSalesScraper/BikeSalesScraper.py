from requests import get
from requests.exceptions import RequestException
from contextlib import closing
from bs4 import BeautifulSoup
import pandas as pd
import unidecode
#import numpy as np
import re
import time


def is_good_response(resp):
    """
    Ensures that the response is a html.
    """
    content_type = resp.headers['Content-Type'].lower()
    return (resp.status_code == 200 and 
            content_type is not None 
            and content_type.find('html') > -1)

def get_html_content(url):
    """
    Retrieve the contents of the url.
    """
    # Be a responisble scraper.
    time.sleep(2)
    headers = {'User-Agent': 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.8.1.6) Gecko/20070725 Firefox/2.0.0.6'}
    # Firefox on Windows: Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.8.1.6) Gecko/20070725 Firefox/2.0.0.6
    # Firefox on Mac: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36
    # Chrome on Linux: Mozilla/5.0 (X11; U; Linux i686; en-US) AppleWebKit/534.3 (KHTML, like Gecko) Chrome/6.0.472.63 Safari/534.3
    # IE on Vista: Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1)




    # Get the html from the url
    try:
        with closing(get(url, stream=True)) as resp:
            content_type = resp.headers['Content-Type'].lower()
            if is_good_response(resp):
                return resp.content
            else:
                # Unable to get the url responce
                return None

    except RequestException as e:
        print('Error during requests to {0} : {1}'.format(url, str(e)))
#        ConnectionError(ProtocolError('Connection aborted.', RemoteDisconnected('Remote end closed connection without response',)),)
#        ConnectionError(ProtocolError('Connection aborted.', OSError("(10060, 'WSAETIMEDOUT')",)),)

def getBikeDetails(htmlContents):
    
    content = htmlContents.find("div", {"class": "content-header"})
    title = content['h1']

    content = htmlContents.find("span", {"class": "price"})
    price = content[0]
    



if __name__ == '__main__':
    '''
    Extraxt data for the sale of motor bikes.
    '''

    baseUrl = 'https://www.bikesales.com.au'
    
    '''Bike Type:
    ATV & Quad >> https://www.bikesales.com.au/bikes/atv-quad/photos-only/
        Agriculture
        Electric
        Fun
        Sport
    Dirt Bikes >> https://www.bikesales.com.au/bikes/dirt-bikes/photos-only/
        Competition
        Electric Bikes
        Enduro 2 Stroke
        Endura 4 Stroke
        Farm
        Fun
        Motocross 2 Stroke
        Motocross 4 Stroke
        Trail
        Trails
    Racing >> https://www.bikesales.com.au/bikes/racing/photos-only/
        Replica
    Road >> https://www.bikesales.com.au/bikes/road/photos-only/
        Adventure Sport
        Adventure Touring
        Cruiser
        Naked
        Scooters
        Sport Touring
        Super Motard
        Super Sport
        Touring
        Vintage
    SxS & UTV >> https://www.bikesales.com.au/bikes/sxs-utv/photos-only/
        Recreational Utility
        Sport
        Utility

    Bike Make
    '''
    # loop over each page
    index = 0
    pagelimit = 50
    offset = index* pagelimit
    
    #roadBikeURL = baseUrl+'road/photots_only/'
    #url = roadBikeURL+extension
    url = baseUrl+'/bikes/?Q=%28Service%3D%5BBikesales%5D%26%28%28%28%28SiloType%3D%5BBrand%20new%20bikes%20available%5D%7CSiloType%3D%5BBrand%20new%20bikes%20in%20stock%5D%29%7CSiloType%3D%5BDealer%20used%20bikes%5D%29%7CSiloType%3D%5BDemo%20%26%20near%20new%20bikes%5D%29%7CSiloType%3D%5BPrivate%20used%20bikes%5D%29%29&Sort=Premium&Offset='+str(offset)+'&Limit='+str(pagelimit)+'&SearchAction=Pagination'
    
    #Search page
    content = get_html_content(url)

    # Get a list of all ski resorts (go through each page)
    html = BeautifulSoup(content, 'html.parser')
    

    '''    pageLinks = html.find("ul", {"id": "pagebrowser1"})
    # Extract the total number of pages
    lastPageNumber = int(re.findall('[0-9][0-9]' ,pageLinks.contents[-2].find('a')['href'])[0])

    # should check for valid 
    return lastPageNumber
    '''

    BikeList = html.findAll("a", {"class": "item-link-container"})
    # Go to bike URL to get the details
    loopindex = 0

    individualBikeURL = BikeList[loopindex].attrs['href']
    BikeContent = get_html_content(baseUrl+individualBikeURL)
    # connection time out error after a few iterations
    #getBikeDetails(BikeContent)

    #getBikeDetails
    content = BeautifulSoup(BikeContent, 'html.parser')

    #bikeHeader = content.find("div", {"class": "content-header"})
    #title = bikeHeader.contents[1].text
    #price = bikeHeader.find("span", {"class": "price"}).text
    # remove any weird charcters like $,*, maybe the comma as well

    #Photos:
    #content.find("a", {"class": "main-image-link"})
    #Multiple list of photos
    #content.find("ul", {"class": "thumbnails jcarousel-list jcarousel-list-horizontal"})

    generalDetails = content.find("section", {"class": "general-details"})

    #print("Slope Statistics:")
    if (generalDetails is not None):
        for row in generalDetails.findAll("tr"):
            
            key = contents[row].contents[1].text
            if (len(contents[row].contents[3]) == 1):
                value = contents[row].contents[3].text
            else:
                value = contents[row].contents[3].find("span", {"class": "price"}).text