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
    time.sleep(2*multiplier)
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
        print("Error during requests to {0} : {1}".format(url, str(e)))
#        ConnectionError(ProtocolError('Connection aborted.', RemoteDisconnected('Remote end closed connection without response',)),)
#        ConnectionError(ProtocolError('Connection aborted.', OSError("(10060, 'WSAETIMEDOUT')",)),)
#        ConnectionResetError(10054, 'An existing connection was forcibly closed by the remote host', None, 10054, None)
       

def getBikeDetails(BikeContent):
    
    content = BeautifulSoup(BikeContent, "html.parser")

    # Photos:
    # content.find("a", {"class": "main-image-link"})
    # Multiple list of photos
    # content.find("ul", {"class": "thumbnails jcarousel-list jcarousel-list-horizontal"})


    details = content.findAll("tr")

    bikeDetails = {}

    if (details is not None):
        for i in range(len(details)):
            
            key = details[i].contents[1].text
            value = details[i].contents[3].text
            
            # Extract numbers from all features that have one, except:
            leaveAsText = ["Bike", "Body", "Configuration", "Reg Plate", "Reg Expiry", "Ref Code", "Stock Number",
                          "Engine Description", "Compression Ratio", "Battery Description", "Wheel Type",
                          "Wheel Size Front", "Wheel Size Rear", "Rear Tyre", "Front Tyre", "Seat Description",
                          "Carburettor", "Exhaust Description", "Transmission Description", "Clutch Type",
                          "Chassis Description", "Front Suspension", "Rear Suspension", "Front Brake Description",
                          "Rear Brake Description", "Instruments / Dash Description", "Exhaust Config",
                          "Primary Drive", "Spark Plug Description", "Ignition Description", 
                          "Economy Mode", "Weight Distribution Front/Rear"]
 
            if (re.sub(r"[^\d.]","",value) != '' and key not in leaveAsText):
                value = re.sub(r"[^\d.]","",value)
           
            if (key == "Final Drive Ratio"):
                if ("/" in value):
                    temp = value.split("/")
                    value = float(temp[0])/float(temp[1])
                elif (":" in value):
                    value = float(value.split(":")[0])
                else:
                    try:
                        value = float(value)
                    except ValueError:
                        continue

            if (key == "Compression Ratio"):
               value = float(value.split(':')[0].split('±')[0])
            
            if (key == "Exhaust Config"):
               value = "'"+re.sub(":","-",value)
            
            if (key == "Last Modified Date"):
                value = datetime.strptime(value,"%d%m%Y")

            if (key == "Reg Expiry"):
                if ("Month" in value):
                    value = int(value.split("Month")[0])
                elif (value != ""):
                    expiry = datetime.strptime(value, '%B %Y')
                    today = datetime.today()
                    deltaDays = (expiry-today).days
                    if (deltaDays < 0):
                        value = 0
                    else:
                        value = int(math.ceil(deltaDays/30))
                else:
                    continue

                    

            if ('Need' not in key and key != "Bike Payment" and key != "Bike Facts" and key != "phone"):
                bikeDetails[key] = value
                # Ignore the listed features


            #print ("{0}: {1}".format(key,value))

    return bikeDetails



if __name__ == '__main__':
    '''
    Extract data for the sale of motor bikes.
    '''

    baseUrl = 'https://www.bikesales.com.au'
    content = get_html_content(baseUrl)
    html = BeautifulSoup(content, 'html.parser')    
    numberOfBikes = html.find("span", {"class": "home-page__stock-counter__count"}).text
    numberOfBikes = float(re.sub(r"[^\d.]","",numberOfBikes))
    pagelimit = 10
    bikeSales = {}

    numberOfPages = math.ceil(numberOfBikes/pagelimit)
   
    
    # loop over each page
    for page in range(2):
        #page = 0
        #https://www.bikesales.com.au/bikes/?Q=%28Service%3D%5BBikesales%5D%26%28%28%28%28SiloType%3D%5BBrand%20new%20bikes%20available%5D%7CSiloType%3D%5BBrand%20new%20bikes%20in%20stock%5D%29%7CSiloType%3D%5BDealer%20used%20bikes%5D%29%7CSiloType%3D%5BDemo%20%26%20near%20new%20bikes%5D%29%7CSiloType%3D%5BPrivate%20used%20bikes%5D%29%29&Sort=Premium&Offset=15&Limit=15&SearchAction=Pagination
        #https://www.bikesales.com.au/bikes/?Q=%28Service%3D%5BBikesales%5D%26%28%28%28%28SiloType%3D%5BBrand%20new%20bikes%20available%5D%7CSiloType%3D%5BBrand%20new%20bikes%20in%20stock%5D%29%7CSiloType%3D%5BDealer%20used%20bikes%5D%29%7CSiloType%3D%5BDemo%20%26%20near%20new%20bikes%5D%29%7CSiloType%3D%5BPrivate%20used%20bikes%5D%29%29&Sort=Premium&Offset=30&Limit=15&SearchAction=Pagination
        #https://www.bikesales.com.au/bikes/?Q=%28Service%3D%5BBikesales%5D%26%28%28%28%28SiloType%3D%5BBrand%20new%20bikes%20available%5D%7CSiloType%3D%5BBrand%20new%20bikes%20in%20stock%5D%29%7CSiloType%3D%5BDealer%20used%20bikes%5D%29%7CSiloType%3D%5BDemo%20%26%20near%20new%20bikes%5D%29%7CSiloType%3D%5BPrivate%20used%20bikes%5D%29%29&Sort=Premium&Offset=45&Limit=15&SearchAction=Pagination
        #
        offset = page* pagelimit
        
        #roadBikeURL = baseUrl+'road/photots_only/'
        #url = roadBikeURL+extension
        url = baseUrl+'/bikes/?Q=%28Service%3D%5BBikesales%5D%26%28%28%28%28SiloType%3D%5BBrand%20new%20bikes%20available%5D%7CSiloType%3D%5BBrand%20new%20bikes%20in%20stock%5D%29%7CSiloType%3D%5BDealer%20used%20bikes%5D%29%7CSiloType%3D%5BDemo%20%26%20near%20new%20bikes%5D%29%7CSiloType%3D%5BPrivate%20used%20bikes%5D%29%29&Sort=Premium&Offset='+str(offset)+'&Limit='+str(pagelimit)+'&SearchAction=Pagination'

        #Search page
        content = get_html_content(url)

        # Get a list of all ski resorts (go through each page)
        html = BeautifulSoup(content, 'html.parser')

        BikeList = html.findAll("a", {"class": "item-link-container"})
        # Go to bike URL to get the details

        bikesPerPage = len(BikeList)
        for loopindex in range(bikesPerPage):
            individualBikeURL = BikeList[loopindex].attrs['href']
            BikeContent = get_html_content(baseUrl+individualBikeURL)
            # reset the miltipler for each new url
            multiplier = 1
            urlDenialCount = 0

            ## occasionally the connection is lost, so try again.
            while (BikeContent == None):
                urlDenialCount += 1
                if (multiplier < 16):
                    multiplier *= 2
                BikeContent = get_html_content(baseUrl+individualBikeURL,multiplier)
            ## Im not sure why the connection is lost, i might be that the site is trying to guard against scraping software.

            ## connection time out error after a few iterations
            bikeDetails = getBikeDetails(BikeContent)

            #getBikeDetails
            #content = BeautifulSoup(BikeContent, 'html.parser')


            print ("{0}: {1}".format(str(loopindex+pagelimit*page), baseUrl+individualBikeURL))
            scrapeDate = datetime.utcnow().strftime("%d-%m-%Y %H:%M")
        
            bikeSales[bikeDetails['Ref Code']] = {"URL": baseUrl+individualBikeURL,
                                                       **bikeDetails,
                                                       "Scraped date": scrapeDate}

    bikeDataFrame = pd.DataFrame.from_dict(bikeSales, orient='index')
    
    # Convert learner approved feature into boolean values
    bikeDataFrame["Learner Approved"] = [False if pd.isnull(a) else True for a in bikeDataFrame['Learner Approved']]
    # Create a seller feature, this assumes that if there is a stock number, the seller is a dealer.
    bikeDataFrame["Seller"] = ["Private" if pd.isnull(a) else "Dealer" for a in bikeDataFrame['Stock Number']]

    bikeDataFrame.to_csv('bikeSales.csv', index=False)
