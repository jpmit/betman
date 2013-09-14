import bfapiparse
from betman import const, Event
from betman.all import betlog

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
    betlog.betlog.info('calling BF API Login')
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
        betlog.betlog.info('calling BF API getActiveEventTypes')        
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
        betlog.betlog.info('calling BF API getAllMarkets')         
        response = self.client.service.getAllMarkets(self.req)
        allmarkets = bfapiparse.ParseMarkets(response)
        
        if const.WRITEDB:
            self.dbman.WriteMarkets(allmarkets,
                                    response.header.timestamp)
        return allmarkets

class APIplaceBets(object):
    def __init__(self, apiclient, dbman):
        self.client = apiclient.client
        self.dbman = dbman
        self.createinput()

    def createinput(self):
        self.req = self.client.factory.create('ns1:PlaceBetsReq')

    def addheader(self):
        self.req.header = self.client.reqheader

    def makebetlist(self, orderlist):
        blist = []

        for o in orderlist:
            # single PlaceBets object
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
            # Starting Price (see BF API docs for more info).
            pbet.betPersistenceType.value = 'IP'
            pbet.marketId = o.mid
            pbet.price = o.price
            pbet.selectionId = o.sid
            pbet.size = o.stake
            # maximum amount of money want to risk for BSP bet (???
            # see BF API docs).
            pbet.bspLiability = 0.0 
            blist.append(pbet)
        return blist
        
    def call(self, orderlist):
        self.addheader()
        self.req.bets.PlaceBets = self.makebetlist(orderlist)
        betlog.betlog.info('calling BF API placeBets')
        response = self.client.service.placeBets(self.req)
        allorders = bfapiparse.ParseplaceBets(response, orderlist)
        
        if const.WRITEDB:
            self.dbman.WriteOrders(allorders,
                                   response.header.timestamp)
        return allorders

# cancelBets doesn't seem to be working
class APIcancelBets(object):
    def __init__(self, apiclient, dbman):
        self.client = apiclient.client
        self.dbman = dbman
        self.createinput()

    def createinput(self):
        self.req = self.client.factory.create('ns1:CancelBetsReq')

    def addheader(self):
        self.req.header = self.client.reqheader

    def getcbets(self, betids):
        cbets = []
        for b in betids:
            cbet = self.client.factory.create('ns1:CancelBets')
            cbet.betId = b
            cbets.append(cbet)
        return cbets
        
    def call(self, betids):
        self.addheader()
        self.req.bets.CancelBets = self.getcbets(betids)
        betlog.betlog.info('calling BF API cancelBets')        
        response = self.client.service.cancelBets(self.req)
        
        if const.WRITEDB:
            # need to update the order here!
            pass

        return response

class APIgetMUBets(object):
    def __init__(self, apiclient, dbman):
        self.client = apiclient.client
        self.dbman = dbman
        self.createinput()

    def createinput(self):
        self.req = self.client.factory.create('ns1:GetMUBetsReq')

    def addheader(self):
        self.req.header = self.client.reqheader

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
        self.req.orderBy.value = 'MATCHED_DATE'
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
        # Note, the actual API call will work if orders=[]. Then we
        # will return all matched and unmatched bets.  However,
        # bfapiparse.ParsegetMUBets will have to be modified to make
        # this work.
        self.addheader()
        betids = [o.oref for o in orders]
        self.fillreq(betids, marketid)

        response = self.client.service.getMUBets(self.req)
        betlog.betlog.info('calling BF API getMUBets')            
        allorders = bfapiparse.ParsegetMUBets(response, orders)
        if const.WRITEDB:
            self.dbman.WriteOrders(allorders, response.header.timestamp)
  
        return allorders

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
        betlog.betlog.info('calling BF API getMarket')        
        response = self.client.service.getMarket(self.req)
        return response

# this is a lite service compared to getMarket above
class APIgetMarketInfo(object):
    def __init__(self, apiclient, dbman):
        self.client = apiclient.client
        self.dbman = dbman
        self.createinput()

    def createinput(self):
        self.req = self.client.factory.create('ns1:GetMarketInfoReq')

    def addheader(self):
        self.req.header = self.client.reqheader
        
    def call(self, mid):
        self.addheader()
        self.req.marketId = mid
        betlog.betlog.info('calling BF API getMarketInfo')
        response = self.client.service.getMarketInfo(self.req)
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
