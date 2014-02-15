from operator import attrgetter
import bfapiparse
from betman import const, Event, betlog
from betman.api.apimethod import ApiMethod

"""
Function for logging into Betfar and classes for calling the Betfair
Api Methods.  These are not designed to be called from user
applications directly; rather, use the interface in bfapi.py by
calling e.g. bfapi.GetActiveEventTypes().
"""

def BFLogin(clglob):
    """
    Login to BF and return RequestHeader that contains session id
    information.
    """
    
    req = clglob.client.factory.create('ns1:LoginReq')
    req.ipAddress = 0
    req.locationId = 0
    req.password = const.BFPASS
    req.productId = 82 # BF Free Api use code
    req.username = const.BFUSER
    req.vendorSoftwareId = 0

    # call the login service
    betlog.betlog.info('calling BF Api Login')
    res = clglob.client.service.login(req)

    # we need the session token from the response
    stoken = res[0].sessionToken
    
    # set up Api request header using the session token
    reqheader = clglob.client.factory.create('ns1:APIRequestHeader')
    reqheader.clientStamp = 0
    reqheader.sessionToken = stoken
    return reqheader

def _add_header(apiclass):
    """
    Add the request header to the ApiMethod object. The most important
    thing this contains is the BF session token to the SOAP request.
    This function is called when making any API request (see any of
    the call methods in the classes below.
    """
    
    apiclass.req.header = apiclass.client.reqheader

# classes that implement the global methods

class ApigetActiveEventTypes(ApiMethod):
    def __init__(self, apiclient):
        super(ApigetActiveEventTypes, self).__init__(apiclient)
        
    def create_req(self):
        self.req = self.client.factory.create('ns1:GetEventTypesReq')
        
    def call(self):
        _add_header(self)
        betlog.betlog.info('calling BF Api getActiveEventTypes')        
        response = self.client.service.getActiveEventTypes(self.req)
        events = bfapiparse.ParsegetActiveEventTypes(response)
        # note that we don't have any database tables for events at
        # the moment - we only write info on actual markets to the
        # database.
        return events

# classes that can be called with either uk or aus exchange

class ApigetAllMarkets(ApiMethod):
    def __init__(self, apiclient, dbman):
        super(ApigetAllMarkets, self).__init__(apiclient)
        self.dbman = dbman

    def create_req(self):
        self.req = self.client.factory.create('ns1:GetAllMarketsReq')
        
    def call(self, ids):
        _add_header(self)
        aofint = self.client.factory.create('ns1:ArrayOfInt')
        aofint.int = ids
        self.req.eventTypeIds = aofint
        betlog.betlog.info('calling BF Api getAllMarkets')         
        response = self.client.service.getAllMarkets(self.req)
        allmarkets = bfapiparse.ParsegetAllMarkets(response)
        
        if const.WRITEDB:
            self.dbman.WriteMarkets(allmarkets,
                                    response.header.timestamp)
        return allmarkets

class ApiplaceBets(ApiMethod):
    def __init__(self, apiclient, dbman):
        super(ApiplaceBets, self).__init__(apiclient)
        self.dbman = dbman

    def create_req(self):
        # we create the request object in the call method instead.
        pass

    def make_bet_list(self, orderlist):
        blist = []

        for o in orderlist:
            # single PlaceBets ApiMethod
            pbet = self.client.factory.create('ns1:PlaceBets')
            # I don't really know what asianLineId is
            pbet.asianLineId = 0
            # back or lay
            if o.polarity == 1:
                pbet.betType.value = 'B'
            elif o.polarity == 2:
                pbet.betType.value = 'L'
            # this can be "E" - exchange bet, "M" - market on close SP
            # bet, "L" Limit on close SP bet or "NONE".
            pbet.betCategoryType.value = 'E'
            # this can be "NONE" - normal exchange or SP bet.
            # Unmatched exchanged bets are lapsed when market turns in
            # play.  Can also be "IP" - in play persistence or "SP" - Moc
            # Starting Price (see BF Api docs for more info).
            pbet.betPersistenceType.value = o.persistence
            pbet.marketId = o.mid
            pbet.price = o.price
            pbet.selectionId = o.sid
            pbet.size = o.stake
            # maximum amount of money want to risk for BSP bet (???
            # see BF Api docs).  Here we are not doing any BSP
            # (Betfair Starting Price) betting, so this does not
            # apply.
            pbet.bspLiability = 0.0 
            blist.append(pbet)
        return blist
        
    def call(self, orderlist):
        # Note: we want this method to be thread-safe.
        _add_header(self)

        # we create req here rather than assigning to self.req in the
        # create_req method for thread-safety.  this means we don't
        # have to manipulate the internal state of the class in this
        # method.
        req = self.client.factory.create('ns1:PlaceBetsReq')

        req.bets.PlaceBets = self.make_bet_list(orderlist)
        betlog.betlog.info('calling BF Api placeBets')
        print 'request follows:'
        print req
        response = self.client.service.placeBets(req)
        allorders = bfapiparse.ParseplaceBets(response, orderlist)
        return allorders

# cancelBets doesn't seem to be working
class ApicancelBets(ApiMethod):
    def __init__(self, apiclient, dbman):
        super(ApicancelBets, self).__init__(apiclient)
        self.dbman = dbman

    def create_req(self):
        self.req = self.client.factory.create('ns1:CancelBetsReq')

    def get_cbets(self, betids):
        cbets = []
        for b in betids:
            cbet = self.client.factory.create('ns1:CancelBets')
            cbet.betId = b
            cbets.append(cbet)
        return cbets
        
    def call(self, betids):
        _add_header(self)
        self.req.bets.CancelBets = self.get_cbets(betids)
        betlog.betlog.info('calling BF Api cancelBets')        
        response = self.client.service.cancelBets(self.req)
        
        if const.WRITEDB:
            # need to update the order here!
            pass

        return response

class ApigetMUBets(ApiMethod):
    def __init__(self, apiclient, dbman):
        super(ApigetMUBets, self).__init__(apiclient)
        self.dbman = dbman

    def create_req(self):
        self.req = self.client.factory.create('ns1:GetMUBetsReq')

    def fillreq(self, betids, marketid):
        # can be C - cancelled, L - lapsed, M - Matched, MU - Matched
        # and Unmatched, S - Settled, U - Unmatched, V - Voided.
        self.req.betStatus = 'MU'
        # if marketid is non-zero, then betids is ignored
        self.req.marketId = marketid
        # can include 200 betids maximum
        self.req.betIds.betId = betids
        # can be BET_ID - order by bet id, CANCELLED_DATE - order by
        # cancelled date, MARKET_NAME - order by market name,
        # MATCHED_DATE - order by Matched date, NONE - default order
        # or PLACED_DATE - order by placed date.  This probably
        # shouldn't matter too much since I'll parse the output
        # anyhow.
        self.req.orderBy.value = 'BET_ID'
        # can be 'ASC' - ascending or 'DESC' - descending.
        self.req.sortOrder.value = 'ASC'
        # I think this is the maximum but docs are unclear.
        self.req.recordCount = 200
        self.req.startRecord = 0
        # apparently we don't need to set matchedSince...
        # self.matchedSince = 
        # not sure what I should go for here...
        self.req.excludeLastSecond = False        
        
    def call(self, orders, marketid=0):
        # Note, the actual Api call will work if orders=[]. Then we
        # will return all matched and unmatched bets.  However,
        # bfapiparse.ParsegetMUBets will have to be modified to make
        # this work.
        _add_header(self)

        # make orders into a dict, where key is order reference
        odict = {}
        for o in orders:
            odict[o.oref] = o
        orders.sort(key = attrgetter('oref'))
        
        betids = sorted([o.oref for o in orders])
        self.fillreq(betids, marketid)

        response = self.client.service.getMUBets(self.req)
        betlog.betlog.info('calling BF Api getMUBets')            
        allorders = bfapiparse.ParsegetMUBets(response, odict)

        if const.WRITEDB:
            self.dbman.WriteOrders(allorders.values(),
                                   response.header.timestamp)
            
        return allorders

class ApigetMarket(ApiMethod):
    def __init__(self, apiclient, dbman):
        super(ApigetMarket, self).__init__(apiclient)
        self.dbman = dbman

    def create_req(self):
        self.req = self.client.factory.create('ns1:GetMarketReq')
        self.req.includeCouponLinks = False
        
    def call(self, mid):
        _add_header(self)
        self.req.marketId = mid
        betlog.betlog.info('calling BF Api getMarket')        
        response = self.client.service.getMarket(self.req)
        return response

# this is a lite service compared to getMarket above
class ApigetMarketInfo(ApiMethod):
    def __init__(self, apiclient, dbman):
        super(ApigetMarketInfo, self).__init__(apiclient)
        self.dbman = dbman

    def create_req(self):
        self.req = self.client.factory.create('ns1:GetMarketInfoReq')
        
    def call(self, mid):
        _add_header(self)
        self.req.marketId = mid
        betlog.betlog.info('calling BF Api getMarketInfo')
        response = self.client.service.getMarketInfo(self.req)
        return response

# not fully implemented yet (do not use)
class ApigetMarketPricesCompressed(ApiMethod):
    def __init__(self, apiclient, dbman):
        super(ApigetMarketPricesCompressed, self).__init__(apiclient)
        self.dbman = dbman

    def create_req(self):
        self.req = self.client.factory.\
                   create('ns1:GetMarketPricesCompressedReq')
        
    def call(self, mid):
        _add_header(self)
        self.req.marketId = mid
        result = self.client.service.getMarketPricesCompressed(self.req)

#        allselections = bffunctions.ParseBFPrices(result)
#        if const.WRITEDB:
#            self.dbman.WriteSelections(allselections, result.header.timestamp)
#        return allmarkets
        
        return result

# not fully implemented yet (do not use)
class ApigetMarketPrices(ApiMethod):
    def __init__(self, apiclient, dbman):
        super(ApigetMarketPrices, self).__init__(apiclient)
        self.dbman = dbman

    def create_req(self):
        self.req = self.client.factory.create('ns1:GetMarketPricesReq')
        
    def call(self, mid):
        _add_header(self)
        self.req.marketId = mid
        result = self.client.service.getMarketPrices(self.req)
        return result
