# betfair.py
# code for logging in to betfair etc

from suds.client import Client
import bffunctions

# try and get working with proxy
d = dict(http='80.243.185.168', https='80.243.185.168')
clientglob = Client('file:///home/jm0037/python/bdaq/code/BFGlobalService.wsdl')
clientglob.set_options(proxy=d)
clientuk = Client('file:///home/jm0037/python/bdaq/code/BFExchangeServiceUK.wsdl')
clientuk.set_options(proxy=d)
clientaus = Client('file:///home/jm0037/python/bdaq/code/BFExchangeServiceAUS.wsdl')
clientaus.set_options(proxy=d)

### login
req = clientglob.factory.create('ns1:LoginReq')
req.ipAddress = 0
req.locationId = 0
req.password = 'Bamb0[]zle'
req.productId = 82
req.username = 'mithen'
req.vendorSoftwareId = 0

res = clientglob.service.login(req)

# we need the session token from the response
stoken = res[0].sessionToken
# set up API request header using this
reqheader = clientglob.factory.create('ns1:APIRequestHeader')
reqheader.clientStamp = 0
reqheader.sessionToken = stoken

### get the events
req2 = clientglob.factory.create('ns1:GetEventTypesReq')
req2.header = reqheader
res2 = clientglob.service.getActiveEventTypes(req2)

### try and get markets and selections for rugby union (id = 5)
req3 = clientglob.factory.create('ns1:GetEventsReq')
req3.header = reqheader
req3.eventParentId = 5
#req3.locale = 0
res3 = clientglob.service.getEvents(req3)

### APPARENTLY SHOULD USE THE GET ALL MARKETS INSTEAD OF ABOVE!
req4 = clientuk.factory.create('ns1:GetAllMarketsReq')
# if we don't do any of this stuff, we will get all markets on the
# exchange automagically!
aofint = clientuk.factory.create('ns1:ArrayOfInt')
aofint.int = [5] # rugby union
req4.header = reqheader
req4.eventTypeIds = aofint

res4 = clientuk.service.getAllMarkets(req4)

### Do same for Aussie exchange
req5 = clientaus.factory.create('ns1:GetAllMarketsReq')
# if we don't do any of this stuff, we will get all markets on the
# exchange automagically!
aofint = clientuk.factory.create('ns1:ArrayOfInt')
aofint.int = [5] # rugby union
req5.header = reqheader
req5.eventTypeIds = aofint

res5 = clientaus.service.getAllMarkets(req5)

# get all markets
ukmarkets = bffunctions.ParseBFMarkets(res4)
ausmarkets = bffunctions.ParseBFMarkets(res5)
allmarkets = ukmarkets + ausmarkets

# next, we need to figure out how to match the market names
# from betdaq and betfair.....

