import requests
import time
import ast
import json
import ebaysdk
from ebaysdk.http import Connection as HTTP
from ebaysdk.exception import ConnectionError
from lxml import html
from urllib.parse import quote
from datetime import datetime as dt

# Scheme
# json response -> get first item url -> open item page and got reviews -> create complete json with all required data
#

#TODO
# Logging 
# Generator format
# Choose format for data ouptup (csv or json) 
# Create separate file for settings

USER_AGENT = 'Mozilla/5.0 (Windows NT 6.3; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36'
SECURITY_APPNAME = 'EugeneSh-bestCoff-PRD-35d7504c4-714318e1'
URL = 'http://svcs.ebay.com/services/search/FindingService/v1?OPERATION-NAME=findItemsByKeywords&SERVICE-VERSION=1.0.0'
global_id_list = ['EBAY-US', 'EBAY-ENCA']
keywords = 'coffee ground'

# Api-call url example:
# http://svcs.ebay.com/services/search/FindingService/v1?OPERATION-NAME=findItemsByKeywords&SERVICE-VERSION=1.1.0&SECURITY-APPNAME=EugeneSh-bestCoff-PRD-35d7504c4-714318e1&GLOBAL-ID=EBAY-ENCA&RESPONSE-DATA-FORMAT=JSON&REST-PAYLOAD&keywords=coffee%20ground&paginationInput.entriesPerPage=1&paginationInput.pageNumber=1
#


class Espider:
    def __init__(self, security_appname, global_id, url, keywords, pages_amount, items_per_page):
        self.security_appname = '&SECURITY-APPNAME=' + security_appname
        self.global_id = '&GLOBAL-ID=' + global_id
        self.url = url
        self.pages_amount = pages_amount
        self.keywords = '&keywords=' + quote(keywords)
        self.items_per_page = '&paginationInput.entriesPerPage=' + str(items_per_page)
        self.complete_api_call_url = self.url + \
                                    self.security_appname + \
                                    self.global_id + \
                                    '&RESPONSE-DATA-FORMAT=JSON&REST-PAYLOAD' + \
                                    self.keywords + \
                                    self.items_per_page + \
                                    '&paginationInput.pageNumber='
                                    
    #According to ebay api docs ebay return maximum 100 pages (paginationInput.pageNumber)
    #and maximum 100 items per page
    
    def GetDataFromContent(self, responseContent):
        """
        This func takes api response, parse it and return data in json format   
        """
        items_amount_in_reponse = int(responseContent['findItemsByKeywordsResponse'][0]['searchResult'][0]['@count'])
        
        for i in range(items_amount_in_reponse):
            #TODO 
            #Make time in tz UTC+2 
            time = dt.now().strftime('%d.%m.%y %H:%M:%S')
            title = responseContent['findItemsByKeywordsResponse'][0]['searchResult'][0]['item'][i]['title'][0]
            price = responseContent['findItemsByKeywordsResponse'][0]['searchResult'][0]['item'][i]['sellingStatus'][0]['currentPrice'][0]['__value__']
            currency = responseContent['findItemsByKeywordsResponse'][0]['searchResult'][0]['item'][i]['sellingStatus'][0]['currentPrice'][0]['@currencyId']
            product_url = responseContent['findItemsByKeywordsResponse'][0]['searchResult'][0]['item'][i]['viewItemURL'][0].replace('\\','')
            
            try:
                product_rating = self.GetProductRating(product_url)
                stars_amount = product_rating[0]
                reviews_amount = product_rating[1]
            except:
                stars_amount = "-"
                reviews_amount = "-"
        
            productimage_url = responseContent['findItemsByKeywordsResponse'][0]['searchResult'][0]['item'][i]['galleryURL'][0].replace('\\','')
            location = responseContent['findItemsByKeywordsResponse'][0]['searchResult'][0]['item'][i]['location'][0]
            
            """
            yield {
                "title": title,
                "price": price,
                "currency": currency,
                "product_url": product_url,
                "stars_amount": stars_amount,
                "reviews_amount": reviews_amount,
                "productimage_url": productimage_url,
                "location": location,
            }
            """
        #print('\n',title,'\n', price,'\n',currency,'\n',product_url,'\n',location,'\n',productimage_url,'\n')
        
            complete_result = {
                "time": time,
                "title": title,
                "price": price,
                "currency": currency,
                "product_url": product_url,
                "site": "ebay",
                "stars_amount": stars_amount,
                "reviews_amount": reviews_amount,
                "productimage_url": productimage_url,
                "location": location,
            }
            
            with open('out.txt', 'a') as f:
                f.write(json.dumps(complete_result) + '\n')
                    
            print(json.dumps(complete_result))
    
    def GetProductRating(self, product_url):
        try:
            headers = {'user-agent' : USER_AGENT}
            res = requests.get(product_url, headers=headers)
        except:
            #print("Error during request/response parse. Url: %s" % product_url)
            return "Error during request. Url: %s" % product_url
            
        tree = html.fromstring(res.content)
        stars_amount = tree.xpath('//*[@class="ebay-content-wrapper"]/span[1][@class="ebay-review-start-rating"]/text()')[0].strip()
        reviews_amount_raw = tree.xpath('//*[@class="ebay-content-wrapper"]/span[@class="ebay-reviews-count"]/text()')[0]
        reviews_amount = "".join([i for i in reviews_amount_raw if i.isdigit()])
        return stars_amount, reviews_amount
        
        """
        except:
            print("Error during request/response parse. Url: %s" % product_url)
        """
    
    def RunSpider(self):
        print("ebaySpider started...\npages_amount: %s\nitems_per_page: %s" % (self.pages_amount, self.items_per_page))
        print("GLOBAL-ID set to %s" % global_id)
        try:
            #api = Finding(appid=SECURITY_APPNAME, config_file=None)
            api = HTTP(config_file=None)
            headers_for_sdk = {'User-Agent': USER_AGENT}
            
            #Make api call
            for pageNumber in range(1, self.pages_amount + 1):
                print("================== Page %s ==================" % pageNumber)
                responseObj = api.execute(self.complete_api_call_url + str(pageNumber), headers=headers_for_sdk)

                if responseObj.status_code != 200:
                    return False

                #Get content part of response obj and convert it to str;
                #Method ast.literal_eval() transform str > dict object.
                responseContent = ast.literal_eval(str(responseObj.content, 'utf-8'))
                self.GetDataFromContent(responseContent)

        except ConnectionError as e:
            print(e)

if __name__ == '__main__':
    try:
        for global_id in global_id_list:
            espider = Espider(security_appname=SECURITY_APPNAME, global_id=global_id, url=URL, keywords=keywords, pages_amount=1, items_per_page=3)
            espider.RunSpider()
    except KeyboardInterrupt:
        print("Spider stoping...")
