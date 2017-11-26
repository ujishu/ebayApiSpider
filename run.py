from ebayApiSpider import Espider
import settings

global_id_list = settings.global_id_list
keywords = "coffee ground"

try:
    for global_id in global_id_list:
        espider = Espider(security_appname=settings.SECURITY_APPNAME, 
                            global_id=global_id, 
                            url=settings.API_CALL_URL, 
                            keywords=keywords)
        espider.run_spider()
except KeyboardInterrupt:
    print("Spider stoping...")