import asyncio
from proxybroker import Broker

"""
This module created for fetch proxys using proxybroker module 
"""

async def show(proxies):
    while True:
        proxy = await proxies.get()
        if proxy is None:
            print("\nproxy is None\n")
            break
        #print('Found proxy: %s' % proxy)
        proxy_type = [key for key in proxy.types][0].lower()
        return (proxy_type, proxy.host, proxy.port)
        
def get_proxy():
    proxies = asyncio.Queue()
    broker = Broker(proxies)
    tasks = asyncio.gather(
        broker.find(types=['HTTP', 'HTTPS'], limit=1),
        show(proxies))

    loop = asyncio.get_event_loop()
    proxy = loop.run_until_complete(tasks)[1]
    #print(proxy)
    return proxy

"""
get_proxy()
get_proxy = get_proxy()
proxies = dict({get_proxy[0]: get_proxy[0] + '://' + get_proxy[1] + ':' + get_proxy[2]})
print(proxies)
"""