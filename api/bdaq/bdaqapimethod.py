from betman import const, util, Event
import datetime
import apiparse

# classes that implement the read only methods,
# in the order that they appear NewExternalAPI spec.doc

class APIListTopLevelEvents(object):
    def __init__(self, apiclient):
        self.client = apiclient.client
        self.setinput()

    def setinput(self):
        self.req = self.client.factory.create('ListTopLevelEventsRequest')
        # this is the default, and I don't exactly know why we would
        # want True anyway, but lets set it just in case
        self.req._WantPlayMarkets = False
        
    def call(self):
        result = self.client.service.ListTopLevelEvents(self.req)
        evs = []
        for ec in result.EventClassifiers:
            evs.append(Event(ec._Name, ec._Id, 1))
        return evs
                
class APIGetEventSubTreeNoSelections(object):
    def __init__(self, apiclient, dbman):
        self.client = apiclient.client
        self.dbman = dbman
        self.setinput()

    def setinput(self):
        self.req = self.client.factory.create(('GetEventSubTreeNoSele'
                                               'ctionsRequest'))
        # may want to change this sometime
        self.req._WantPlayMarkets = False

    def call(self, ids, direct=True):
        self.req.EventClassifierIds = ids
        self.req._WantDirectDescendentsOnly = direct
        result = self.client.service.GetEventSubTreeNoSelections(self.req)
        allmarkets =  apiparse.ParseEventSubTree(result)
        if const.WRITEDB:
            self.dbman.WriteMarkets(allmarkets, result.Timestamp)
        return allmarkets
                
class APIGetEventSubTreeWithSelections(object):
    def __init__(self, apiclient):
        self.client = apiclient.client
        self.setinput()

    def setinput(self):
        self.req = self.client.factory.create('GetEventSubTreeWithSelectionsRequest')
        # note that for this function (unlike NoSelections),
        # can only go down one level
        # i.e. can only get 'direct descendants'
        self.req._WantPlayMarkets = False

    def call(self, ids):
        self.req.EventClassifierIds = ids
        result = self.client.service.GetEventSubTreeWithSelections(self.req)
        return result

class APIGetMarketInformation(object):
    def __init__(self, apiclient):
        self.client = apiclient.client
        self.setinput()

    def setinput(self):
        self.req = self.client.factory.create('GetMarketInformationRequest')

    def call(self, ids):
        self.req.MarketIds = ids
        result = self.client.service.GetMarketInformation(self.req)
        return result

class APIListSelectionsChangedSince(object):
    def __init__(self, apiclient):
        self.client = apiclient.client
        self.setinput()

    def setinput(self):
        self.req = self.client.factory.create('ListSelectionsChangedSinceRequest')

    def call(self, seqnum):
        self.req._SelectionSequenceNumber = seqnum
        result = self.client.service.ListSelectionsChangedSince(self.req)
        return result

class APIListMarketWithdrawalHistory(object):
    def __init__(self, apiclient):
        self.client = apiclient.client
        self.setinput()

    def setinput(self):
        self.req = self.client.factory.create('ListMarketWithdrawalHistoryRequest')

    def call(self, ids):
        self.req.MarketId = ids
        result = self.client.service.ListMarketWithdrawalHistory(self.req)
        return result

class APIGetPrices(object):
    def __init__(self, apiclient, dbman):
        self.client = apiclient.client
        self.dbman = dbman
        self.setinput()

    def setinput(self):
        self.req = self.client.factory.create('GetPricesRequest')
        self.req._ThresholdAmount = 0.0
        # -1 for all prices, 0 for no prices, or a positive
        # number for a maximum number of prices
        self.req._NumberForPricesRequired = const.NUMPRICES
        self.req._NumberAgainstPricesRequired = const.NUMPRICES
        self.req._WantMarketMatchedAmount = True
        self.req._WantSelectionsMatchedAmounts = True
        self.req._WantSelectionMatchedDetails = True

    def call(self, mids):
        """markets should be list of market ids"""
        MAXMIDS = 50 # set by BDAQ API
        allselections = []
        # split up mids into groups of size MAXMIDS
        for ids in util.chunks(mids, MAXMIDS):
            self.req.MarketIds = ids
            result = self.client.service.GetPrices(self.req)
            selections =  apiparse.ParsePrices(ids, result)
            allselections = allselections + selections
        if const.WRITEDB:
            self.dbman.WriteSelections(allselections, result.Timestamp)
        return allselections

    def process(self, result):
        # get from the raw SOAP 'object' to
        self.lasttime = result.Timestamp
        # go through each selection in turn keys in data are selection
        # ID, each item in dict is itself a dictionary with the name
        # and prices of the selection.
        self.data = {}
        for sel in result.MarketPrices.Selections:
            # dictionary for this particular selection
            seldata = {'name': sel._Name,
                       'fprices': [],
                       'aprices': []}
            # note that the prices returned from BDAQ API are
            # sorted.
            for price in sel.ForSidePrices:
                seldata['fprices'].append((price._Price, price._Stake))
            for price in sel.AgainstSidePrices:
                seldata['aprices'].append((price._Price, price._Stake))
            # add the selection data to main dict
            self.data[str(sel._Id)] = seldata
        return

class APIGetOddsLadder(object):
    pass

class APIGetCurrentSelectionSequenceNumber(object):
    def __init__(self, apiclient):
        self.client = apiclient.client
        self.setinput()

    def setinput(self):
        #self.req = None
        pass

    def call(self):
        result = self.client.service.GetCurrentSelectionSequenceNumber()
        return result

####################
# These ones should be called with the secure client !!
####################

class APIGetAccountBalances(object):
    def __init__(self, apiclient):
        self.client = apiclient.client
        self.setinput()

    def setinput(self):
        #self.req = None
        pass

    def call(self):
        result = self.client.service.GetAccountBalances()
        return result

class APIListAccountPostings(object):
    def __init__(self, apiclient):
        self.client = apiclient.client
        self.setinput()

    def setinput(self):
        self.req = self.client.factory.create('ListAccountPostingsRequest')

    def call(self, *args):
        # should be able to pass two datetime objects here(?)
        # year month day hour minute second microsecond
        nargs = len(args)
        if nargs > 0:
            self.req._StartTime = args[0]
            if nargs > 1:
                self.req._EndTime = args[1]
            else:
                self.req._Endtime = datetime.datetime.now()
        else:
            # no args supplied, default starttime to 1 day ago,
            # endtime to now
            self.req._EndTime = datetime.datetime.now()
            self.req._StartTime = (self.req._EndTime -
                                  datetime.timedelta(days=1))
        result = self.client.service.ListAccountPostings(self.req)
        return result

# class APIListAccountPostingsById(object):

# class APIChangePassword(object):

class APIListOrdersChangedSince(object):
    def __init__(self, apiclient):
        self.client = apiclient.client
        self.setinput()

    def setinput(self):
        self.req = self.client.factory.create('ListOrdersChangedSinceRequest')

    def call(self, snum):
        # the sequence number should come in the first instance from
        # the bootstrap which is next class
        self.req.SequenceNumber = snum
        result = self.client.service.ListOrdersChangedSince(self.req)
        return result

class APIListBootstrapOrders(object):
    def __init__(self, apiclient):
        self.client = apiclient.client
        self.setinput()

    def setinput(self):
        self.req = self.client.factory.create('ListBootstrapOrdersRequest')
        # not currently sure what the best default is here
        self.req.wantSettledOrdersOnUnsettledMarkets = True

    def call(self, snum=-1):
        # the sequence number should come in the first instance from
        # the bootstrap which is next class
        self.req.SequenceNumber = snum
        result = self.client.service.ListBootstrapOrders(self.req)
        return result

class APIGetOrderDetails(object):
    def __init__(self, apiclient):
        self.client = apiclient.client
        self.setinput()

    def setinput(self):
        self.req = self.client.factory.create('GetOrderDetailsRequest')

    def call(self, oid):
        self.req._OrderId = oid
        result = self.client.service.GetOrderDetails(self.req)
        return result

class APIPlaceOrdersNoReceipt(object):
    def __init__(self, apiclient):
        self.client = apiclient.client
        self.setinput()

    def setinput(self):
        self.req = self.client.factory.create('PlaceOrdersNoReceiptRequest')
        # if one fails, none will be placed
        self.req.WantAllOrNothingBehaviour = True
        # lets just do a single order at a time at the moment
        self.order = self.client.factory.create('SimpleOrderRequest')

    def makeorder(self, odict):
        for k in odict:
            setattr(self.order, k, odict[k])

    def call(self, order):
        # order passed should be a dict with keys
        # see 'ordertest.py' for what the dict should contain
        self.makeorder(order)
        self.req.Orders.Order = [self.order]
        print self.req
        result = self.client.service.PlaceOrdersNoReceipt(self.req)
        return result

class APIPlaceOrdersWithReceipt(object):
    def __init__(self, apiclient):
        self.client = apiclient.client
        self.setinput()

    def setinput(self):
        self.req = self.client.factory.create('PlaceOrdersWithReceiptRequest')
        # lets just do a single order at a time at the moment
        self.order = self.client.factory.create('SimpleOrderRequest')

    def makeorder(self, odict):
        for k in odict:
            setattr(self.order, k, odict[k])

    def call(self, order):
        # order passed should be a dict with keys
        # see 'ordertest.py' for what the dict should contain
        self.makeorder(order)
        self.req.Orders.Order = [self.order]
        print self.req
        result = self.client.service.PlaceOrdersWithReceipt(self.req)
        return result

#class APIUpdateOrdersNoReceipt(object):

#class APICancelOrders(object):

#class APICancelAllOrdersOnMarket(object):

#class APICancelAllOrders(object):

#class APIListBlackListInformation(object):

####################
# Suspending orders
####################

#class APISuspendFromTrading(object):

#class APIUnsuspendFromTrading(object):

#class APISuspendOrders(object):

#class APISuspendAllOrdersOnMarket(object):

#class APISuspendAllOrders(object):

#class APIUnsuspendOrders(object):

#####################
# Hearbeat stuff
# don't bother with all this for now
####################

#class APIRegisterHeartbeat(object):

#class APIChangeHeartbeatRegistration(object):

#class APIDeregisterHeartbeat(object):

#class APIPulse(object):
