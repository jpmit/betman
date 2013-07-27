import bffunctions
from betman import *

def BFLogin(clglob):
    """Login to BF and return RequestHeader that
    contains session id information."""
    req = clglob.client.factory.create('ns1:LoginReq')
    req.ipAddress = 0
    req.locationId = 0
    req.password = const.BFPASS
    req.productId = 82 # BF Free API use code
    req.username = const.BFUSER
    req.vendorSoftwareId = 0

    # call the login service
    res = clglob.client.service.login(req)

    # we need the session token from the response
    stoken = res[0].sessionToken
    # set up API request header using this
    reqheader = clglob.client.factory.create('ns1:APIRequestHeader')
    reqheader.clientStamp = 0
    reqheader.sessionToken = stoken
    return reqheader

# classes that implement the global methods

class APIgetActiveEventTypes(object):
    def __init__(self, apiclient):
        self.client = apiclient.client
        self.setinput()

    def setinput(self):
        self.req = self.client.factory.create('ns1:GetEventTypesReq')
        self.req.header = self.client.reqheader
        
    def call(self):
        result = self.client.service.getActiveEventTypes(self.req)
        evs = []
        for e in result.eventTypeItems.EventType:
            evs.append(Event(e.name, e.id, 2))
        return evs

# classes that can be called with either uk or aus exchange

class APIgetAllMarkets(object):
    def __init__(self, apiclient, dbman):
        self.client = apiclient.client
        self.dbman = dbman
        self.setinput()

    def setinput(self):
        self.req = self.client.factory.create('ns1:GetAllMarketsReq')
        self.req.header = self.client.reqheader
        
    def call(self, ids):
        aofint = self.client.factory.create('ns1:ArrayOfInt')
        aofint.int = ids
        self.req.eventTypeIds = aofint
        result = self.client.service.getAllMarkets(self.req)
        allmarkets = bffunctions.ParseBFMarkets(result)
        
        if const.WRITEDB:
            self.dbman.WriteMarkets(allmarkets, result.header.timestamp)
        return allmarkets

class APIgetMarket(object):
    def __init__(self, apiclient, dbman):
        self.client = apiclient.client
        self.dbman = dbman
        self.setinput()

    def setinput(self):
        self.req = self.client.factory.create('ns1:GetMarketReq')
        self.req.includeCouponLinks = False
        self.req.header = self.client.reqheader
        
    def call(self, mid):
        self.req.marketId = mid
        result = self.client.service.getMarket(self.req)
        return result

class APIgetMarketPricesCompressed(object):
    def __init__(self, apiclient, dbman):
        self.client = apiclient.client
        self.dbman = dbman
        self.setinput()

    def setinput(self):
        self.req = self.client.factory.create('ns1:GetMarketPricesCompressedReq')
        self.req.header = self.client.reqheader
        
    def call(self, mid):
        self.req.marketId = mid
        result = self.client.service.getMarketPricesCompressed(self.req)
        return result
#        allselections = bffunctions.ParseBFPrices(result)
        
#        if const.WRITEDB:
#            self.dbman.WriteSelections(allselections, result.header.timestamp)
#        return allmarkets

class APIgetMarketPrices(object):
    def __init__(self, apiclient, dbman):
        self.client = apiclient.client
        self.dbman = dbman
        self.setinput()

    def setinput(self):
        self.req = self.client.factory.create('ns1:GetMarketPricesReq')
        self.req.header = self.client.reqheader
        
    def call(self, mid):
        self.req.marketId = mid
        result = self.client.service.getMarketPrices(self.req)
        return result
