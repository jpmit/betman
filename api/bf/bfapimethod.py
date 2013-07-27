import bfapiparse
from betman import const, Event 

def BFLogin(clglob):
    """Login to BF and return RequestHeader that contains session id
    information."""
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
        self.createinput()
        
    def createinput(self):
        self.req = self.client.factory.create('ns1:GetEventTypesReq')

    def addheader(self):
        """The header contains the session token"""
        self.req.header = self.client.reqheader
        
    def call(self):
        self.addheader()
        response = self.client.service.getActiveEventTypes(self.req)
        events = bfapiparse.ParseEvents(response)
        # note that we don't have any database tables for events at
        # the moment - we only write info on actual markets to the
        # database.
        return events

# classes that can be called with either uk or aus exchange

class APIgetAllMarkets(object):
    def __init__(self, apiclient, dbman):
        self.client = apiclient.client
        self.dbman = dbman
        self.createinput()

    def createinput(self):
        self.req = self.client.factory.create('ns1:GetAllMarketsReq')

    def addheader(self):
        self.req.header = self.client.reqheader
        
    def call(self, ids):
        self.addheader()
        aofint = self.client.factory.create('ns1:ArrayOfInt')
        aofint.int = ids
        self.req.eventTypeIds = aofint
        response = self.client.service.getAllMarkets(self.req)
        allmarkets = bfapiparse.ParseMarkets(response)
        
        if const.WRITEDB:
            self.dbman.WriteMarkets(allmarkets,
                                    response.header.timestamp)
        return allmarkets

class APIgetMarket(object):
    def __init__(self, apiclient, dbman):
        self.client = apiclient.client
        self.dbman = dbman
        self.createinput()

    def createinput(self):
        self.req = self.client.factory.create('ns1:GetMarketReq')
        self.req.includeCouponLinks = False

    def addheader(self):
        self.req.header = self.client.reqheader
        
    def call(self, mid):
        self.addheader()
        self.req.marketId = mid
        response = self.client.service.getMarket(self.req)
        return response

# not fully implemented yet (do not use)
class APIgetMarketPricesCompressed(object):
    def __init__(self, apiclient, dbman):
        self.client = apiclient.client
        self.dbman = dbman
        self.createinput()

    def createinput(self):
        self.req = self.client.factory.create('ns1:GetMarketPricesCompressedReq')

    def addheader(self):
        self.req.header = self.client.reqheader
        
    def call(self, mid):
        self.addheader()
        self.req.marketId = mid
        result = self.client.service.getMarketPricesCompressed(self.req)
        # 
#        allselections = bffunctions.ParseBFPrices(result)
#        if const.WRITEDB:
#            self.dbman.WriteSelections(allselections, result.header.timestamp)
#        return allmarkets
        
        return result

# not fully implemented yet (do not use)
class APIgetMarketPrices(object):
    def __init__(self, apiclient, dbman):
        self.client = apiclient.client
        self.dbman = dbman
        self.createinput()

    def createinput(self):
        self.req = self.client.factory.create('ns1:GetMarketPricesReq')

    def addheader(self):
        self.req.header = self.client.reqheader
        
    def call(self, mid):
        self.addheader()
        self.req.marketId = mid
        result = self.client.service.getMarketPrices(self.req)
        return result
