from betman import const, util, Event
import datetime
import bdaqapiparse

######################################################################
# classes that implement the read only methods, in the order that    # 
# they appear NewExternalAPIspec.doc                                 #
######################################################################

class APIListTopLevelEvents(object):
    def __init__(self, apiclient):
        self.client = apiclient.client
        self.createinput()

    def createinput(self):
        self.req = self.client.factory.create('ListTopLevelEventsRequest')
        # this is the default, and I don't exactly know why we would
        # want True anyway, but lets set it just in case
        self.req._WantPlayMarkets = False
        
    def call(self):
        response = self.client.service.ListTopLevelEvents(self.req)
        events = bdaqapiparse.ParseEvents(response)
        # note that there is no database table for events at the
        # moment, only for markets
        return events
                
class APIGetEventSubTreeNoSelections(object):
    def __init__(self, apiclient, dbman):
        self.client = apiclient.client
        self.dbman = dbman
        self.createinput()

    def createinput(self):
        self.req = self.client.factory.create(('GetEventSubTreeNoSele'
                                               'ctionsRequest'))
        # may want to change this sometime
        self.req._WantPlayMarkets = False

    def call(self, ids, direct=False):
        self.req.EventClassifierIds = ids
        self.req._WantDirectDescendentsOnly = direct
        response = self.client.service.GetEventSubTreeNoSelections(self.req)
        allmarkets =  bdaqapiparse.ParseEventSubTree(response)
        if const.WRITEDB:
            self.dbman.WriteMarkets(allmarkets, response.Timestamp)
        return allmarkets

# not fully implemented (do not use)
class APIGetEventSubTreeWithSelections(object):
    def __init__(self, apiclient):
        self.client = apiclient.client
        self.createinput()

    def createinput(self):
        self.req = self.client.factory.create('GetEventSubTreeWithSelectionsRequest')
        # note that for this function (unlike NoSelections), can only
        # go down one level i.e. can only get 'direct descendants'
        self.req._WantPlayMarkets = False

    def call(self, ids):
        self.req.EventClassifierIds = ids
        result = self.client.service.GetEventSubTreeWithSelections(self.req)
        return result

# not fully implemented (do not use)
class APIGetMarketInformation(object):
    def __init__(self, apiclient):
        self.client = apiclient.client
        self.createinput()

    def createinput(self):
        self.req = self.client.factory.create('GetMarketInformationRequest')

    def call(self, ids):
        self.req.MarketIds = ids
        result = self.client.service.GetMarketInformation(self.req)
        return result

# not fully implemented (do not use)
class APIListSelectionsChangedSince(object):
    def __init__(self, apiclient):
        self.client = apiclient.client
        self.createinput()

    def createinput(self):
        self.req = self.client.factory.create('ListSelectionsChangedSinceRequest')

    def call(self, seqnum):
        self.req._SelectionSequenceNumber = seqnum
        result = self.client.service.ListSelectionsChangedSince(self.req)
        return result

# not fully implemented (do not use)
class APIListMarketWithdrawalHistory(object):
    def __init__(self, apiclient):
        self.client = apiclient.client
        self.createinput()

    def createinput(self):
        self.req = self.client.factory.create('ListMarketWithdrawalHistoryRequest')

    def call(self, ids):
        self.req.MarketId = ids
        result = self.client.service.ListMarketWithdrawalHistory(self.req)
        return result

class APIGetPrices(object):
    def __init__(self, apiclient, dbman):
        self.client = apiclient.client
        self.dbman = dbman
        self.createinput()

    def createinput(self):
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
            selections =  bdaqapiparse.ParsePrices(ids, result)
            allselections = allselections + selections
        if const.WRITEDB:
            # collapse list of lists to a flat list
            print allselections
            writeselections = [i for sub in allselections for i in sub]
            self.dbman.WriteSelections(writeselections, result.Timestamp)
        return allselections

# not fully implemented (do not use)
class APIGetOddsLadder(object):
    pass

# not fully implemented (do not use)
class APIGetCurrentSelectionSequenceNumber(object):
    def __init__(self, apiclient):
        self.client = apiclient.client
        self.createinput()

    def createinput(self):
        #self.req = None
        pass

    def call(self):
        result = self.client.service.GetCurrentSelectionSequenceNumber()
        return result


######################################################################
# classes that implement the secure methods, in the order that they  # 
# appear NewExternalAPIspec.doc                                      #
######################################################################

# not fully implemented (do not use)
class APIGetAccountBalances(object):
    def __init__(self, apiclient):
        self.client = apiclient.client
        self.createinput()

    def createinput(self):
        #self.req = None
        pass

    def call(self):
        result = self.client.service.GetAccountBalances()
        return result

# not fully implemented (do not use)
class APIListAccountPostings(object):
    def __init__(self, apiclient):
        self.client = apiclient.client
        self.createinput()

    def createinput(self):
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

# not fully implemented (do not use)
class APIListOrdersChangedSince(object):
    def __init__(self, apiclient):
        self.client = apiclient.client
        self.createinput()

    def createinput(self):
        self.req = self.client.factory.create('ListOrdersChangedSinceRequest')

    def call(self, snum):
        # the sequence number should come in the first instance from
        # the bootstrap which is next class
        self.req.SequenceNumber = snum
        result = self.client.service.ListOrdersChangedSince(self.req)
        return result

# not fully implemented (do not use)
class APIListBootstrapOrders(object):
    def __init__(self, apiclient):
        self.client = apiclient.client
        self.createinput()

    def createinput(self):
        self.req = self.client.factory.create('ListBootstrapOrdersRequest')
        # not currently sure what the best default is here
        self.req.wantSettledOrdersOnUnsettledMarkets = True

    def call(self, snum=-1):
        # the sequence number should come in the first instance from
        # the bootstrap which is next class
        self.req.SequenceNumber = snum
        result = self.client.service.ListBootstrapOrders(self.req)
        return result

# not fully implemented (do not use)
class APIGetOrderDetails(object):
    def __init__(self, apiclient):
        self.client = apiclient.client
        self.createinput()

    def createinput(self):
        self.req = self.client.factory.create('GetOrderDetailsRequest')

    def call(self, oid):
        self.req._OrderId = oid
        result = self.client.service.GetOrderDetails(self.req)
        return result

# not fully implemented (do not use)
class APIPlaceOrdersNoReceipt(object):
    def __init__(self, apiclient):
        self.client = apiclient.client
        self.createinput()

    def createinput(self):
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

# not fully implemented (do not use)
class APIPlaceOrdersWithReceipt(object):
    def __init__(self, apiclient):
        self.client = apiclient.client
        self.createinput()

    def createinput(self):
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
