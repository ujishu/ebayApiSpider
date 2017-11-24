import requests
import time
import ast
import json
import ebaysdk
import settings
import uuid
from proxyBroker import get_proxy
from ebaysdk.http import Connection
from ebaysdk.exception import ConnectionError
from lxml import html
from urllib.parse import quote
from datetime import datetime as dt
from user_agents import user_agents_list
from random import randrange
from requests import Request

# Scheme
# json response -> get first item url -> open item page and got reviews -> create complete json with all required data
#

#TODO
# replayce ebaysdk with requests ?
# create separate file for spider instances
# make output in postgres db
# Logging 
# courutin format ?

USER_AGENT_LIST = user_agents_list.split('\n')
SECURITY_APPNAME = settings.SECURITY_APPNAME
URL = settings.API_CALL_URL
global_id_list = settings.global_id_list
keywords = 'coffee ground'

# Api-call url example:
# http://svcs.ebay.com/services/search/FindingService/v1?OPERATION-NAME=findItemsByKeywords&SERVICE-VERSION=1.1.0&SECURITY-APPNAME=EugeneSh-bestCoff-PRD-35d7504c4-714318e1&GLOBAL-ID=EBAY-ENCA&RESPONSE-DATA-FORMAT=JSON&REST-PAYLOAD&keywords=coffee%20ground&paginationInput.entriesPerPage=1&paginationInput.pageNumber=1
#

class OverridedConnectionClass(Connection):
    """
    This class override ebaysdk.http.Connection class for using random user_agents in api calls 
    """
    def build_request(self, url, data, headers):
        self._request_id = uuid.uuid4()
        
        global USER_AGENT_LIST
        USER_AGENT = USER_AGENT_LIST[randrange(0,len(USER_AGENT_LIST))]
        print("user agent in OverridedConnectionClass ", USER_AGENT)

        headers.update({'User-Agent': USER_AGENT,
                        'X-EBAY-SDK-REQUEST-ID': str(self._request_id)})

        kw = dict()
        if self.method == 'POST':
            kw['data'] = data
        else:
            kw['params'] = data

        request = Request(self.method,
                          url,
                          headers=headers,
                          **kw
                          )

        self.request = request.prepare()


class Espider:
    def __init__(self, security_appname, global_id, url, keywords, items_per_page):
        self.security_appname = '&SECURITY-APPNAME=' + security_appname
        self.global_id = '&GLOBAL-ID=' + global_id
        self.url = url
        self.pages_amount = 100
        self.keywords = '&keywords=' + quote(keywords)
        self.items_per_page = '&paginationInput.entriesPerPage=' + str(items_per_page)
        self.complete_api_call_url = self.url + \
                                    self.security_appname + \
                                    self.global_id + \
                                    '&RESPONSE-DATA-FORMAT=JSON&REST-PAYLOAD' + \
                                    self.keywords + \
                                    self.items_per_page + \
                                    '&paginationInput.pageNumber='
        self.output_json_filename = 'espider_' + dt.now().strftime('%d-%m-%y_%H%M%S') + '_output.json' 
    
    #                                
    # According to ebay api docs ebay return maximum 100 pages (paginationInput.pageNumber)
    # and maximum 100 items per page
    #
    
    def getDataFromContent(self, responseContent):
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
                product_rating = self.getProductRating(product_url)
                stars_amount = product_rating[0]
                reviews_amount = product_rating[1]
            except:
                stars_amount = "-"
                reviews_amount = "-"
                
            try:
                productimage_url = responseContent['findItemsByKeywordsResponse'][0]['searchResult'][0]['item'][i]['galleryURL'][0].replace('\\','')
            except KeyError:
                print("\nKeyError in productimage_url\n")
                
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
            
            with open(self.output_json_filename, 'a') as f:
                f.write(json.dumps(complete_result) + ',\n')
                    
            print(json.dumps(complete_result))
    
    def getProductRating(self, product_url):
        
        global USER_AGENT_LIST
        USER_AGENT = USER_AGENT_LIST[randrange(0,len(USER_AGENT_LIST))]
        print("user agent in getProductRating  ", USER_AGENT)
        
        get_proxy = get_proxy()
        proxies = dict({get_proxy[0]: get_proxy[0] + '://' + get_proxy[1] + ':' + str(get_proxy[2])})
        
        try:
            headers = {'user-agent' : USER_AGENT}
            res = requests.get(product_url, headers=headers, proxies=proxies, timeout=30)
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
    
    def runSpider(self):
        
        print("ebaySpider started...\npages_amount: %s\nitems_per_page: %s" % (self.pages_amount, self.items_per_page))
        print("GLOBAL-ID set to %s" % global_id)
        
        proxy = get_proxy()
        
        try:
            api = OverridedConnectionClass(config_file=None, proxy_host=proxy[1], proxy_port=proxy[2])
            
            #Make api call
            for pageNumber in range(1, self.pages_amount + 1):
                print("================== Page %s ==================" % pageNumber)
                responseObj = api.execute(self.complete_api_call_url + str(pageNumber))

                if responseObj.status_code != 200:
                    return False

                #Get content part of response obj and convert it to str;
                #Method ast.literal_eval() transform str > dict object.
                
                responseContent = ast.literal_eval(str(responseObj.content, 'utf-8'))
                self.getDataFromContent(responseContent)

        except ConnectionError as e:
            print(e)

if __name__ == '__main__':
    try:
        for global_id in global_id_list:
            espider = Espider(security_appname=SECURITY_APPNAME, global_id=global_id, url=URL, keywords=keywords, items_per_page=100)
            espider.runSpider()
    except KeyboardInterrupt:
        print("Spider stoping...")
