import datetime
import time
from betman import const, util, Event
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
        # TODO:
        # the markets in allmarkets are currently ordered by
        # Event ID.  But we may have passed the event ids in a
        # different order.  Let's reorder the markets so that they are
        # in the event id order as passed to this function (parameter
        # ids).
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

class APIGetMarketInformation(object):
    def __init__(self, apiclient, dbman):
        self.client = apiclient.client
        self.dbman = dbman
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
    def __init__(self, apiclient, dbman, throttl=0):
        self.client = apiclient.client
        self.dbman = dbman
        # time to wait between consecutive calls when calling multiple
        # times.
        self.throttl = throttl
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
        for (callnum, ids) in enumerate(util.chunks(mids, MAXMIDS)):
            self.req.MarketIds = ids
            if callnum > 0:
                # sleep for some time before calling API again
                time.sleep(self.throttl)
            if const.DEBUG:
                print 'calling GetPrices'                
            result = self.client.service.GetPrices(self.req)
            selections =  bdaqapiparse.ParsePrices(ids, result)
            allselections = allselections + selections

        if const.WRITEDB:
            # collapse list of lists to a flat list
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

class APIGetAccountBalances(object):
    def __init__(self, apiclient, dbman):
        self.client = apiclient.client
        self.dbman = dbman

    def createinput(self):
        pass

    def call(self):
        result = self.client.service.GetAccountBalances()
        # accountinfo returns a tuple (_AvailableFunds, _Balance,
        #                              _Credit, _Exposure)
        accinfo = bdaqapiparse.ParseGetAccountBalances(result)
        if const.WRITEDB:
            self.dbman.WriteAccountBalance(const.BDAQID, accinfo,
                                           result.Timestamp)

        return accinfo

# not fully implemented (do not use)
# this one lists extra details about account, mainly orders settled
# between two dates.

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
            # no args supplied, default starttime to 7 days ago,
            # endtime to now
            self.req._EndTime = datetime.datetime.now()
            self.req._StartTime = (self.req._EndTime -
                                  datetime.timedelta(days=7))
        result = self.client.service.ListAccountPostings(self.req)
        return result

# class APIListAccountPostingsById(object):

# class APIChangePassword(object):

# not fully implemented (do not use)
class APIListOrdersChangedSince(object):
    def __init__(self, apiclient, dbman):
        self.client = apiclient.client
        self.dbman = dbman
        self.createinput()

    def createinput(self):
        self.req = self.client.factory.create('ListOrdersChangedSinceRequest')

    def call(self, seqnum=None):
        global ORDER_SEQUENCE_NUMBER
        # the sequence number should come in the first instance from
        # the bootstrap, see class APIListBootstrapOrders
        if seqnum:
            self.req.SequenceNumber = seqnum
        else:
            self.req.SequenceNumber = ORDER_SEQUENCE_NUMBER
        if const.DEBUG:
            print 'Calling ListOrders with sequence number: {0}'\
                  .format(self.req.SequenceNumber)
        
        resp = self.client.service.ListOrdersChangedSince(self.req)

        if const.DEBUG:
            print resp

        data = bdaqapiparse.ParseListOrdersChangedSince(resp)
        if not data:
            # should be returning an empty list here, i.e. no orders
            # changed since last call.
            return data
        # if we did get some orders changed, the data consists of the
        # order information and the new max sequence number.
        orders, snum = data
        # set order sequence number to the maximum one returned by API
        ORDER_SEQUENCE_NUMBER = snum        
        if const.DEBUG:
            print 'Setting sequence number to: {0}'\
                  .format(snum)

        # update changed orders
        if const.WRITEDB:
            self.dbman.WriteOrders(orders, resp.Timestamp)
        return orders

# this sequence number is updated by both APIListOrdersChangedSince
# (above) and APIListBootstrapOrders (below).
ORDER_SEQUENCE_NUMBER = -1

class APIListBootstrapOrders(object):
    def __init__(self, apiclient, dbman):
        self.client = apiclient.client
        self.dbman = dbman
        
        self.createinput()

    def createinput(self):
        self.req = self.client.factory.create('ListBootstrapOrdersRequest')
        # this is probably the best default here (see BDAQ documentation)
        self.req.wantSettledOrdersOnUnsettledMarkets = False

    def call(self, snum=-1):
        # the sequence number should come in the first instance from
        # the bootstrap which is next class
        global ORDER_SEQUENCE_NUMBER
        self.req.SequenceNumber = ORDER_SEQUENCE_NUMBER
        result = self.client.service.ListBootstrapOrders(self.req)
        # assign sequence number we get back to ORDER_SEQUENCE_NUMBER
        ORDER_SEQUENCE_NUMBER = result._MaximumSequenceNumber
        allorders = bdaqapiparse.ParseListBootstrapOrders(result)
        if const.WRITEDB:
            self.dbman.WriteOrders(allorders, result.Timestamp)
        return allorders

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

class APIPlaceOrdersNoReceipt(object):
    def __init__(self, apiclient, dbman):
        self.client = apiclient.client
        self.dbman = dbman
        self.createinput()

    def createinput(self):
        self.req = self.client.factory.create('PlaceOrdersNoReceiptRequest')
        # if one fails, none will be placed
        self.req.WantAllOrNothingBehaviour = True

    def makeorderlist(self, orderlist):
        olist = []

        for o in orderlist:
            # make a single order object
            order = self.client.factory.create('SimpleOrderRequest')

            order._SelectionId = o.sid
            order._Stake = o.stake
            order._Price = o.price
            order._Polarity = o.polarity
            # we probably need to look at the market information to put
            # this stuff in correctly
            order._ExpectedSelectionResetCount = 1
            order. _ExpectedWithdrawalSequenceNumber = 0,         
            order._CancelOnInRunning = True
            order._CancelIfSelectionReset = True

            olist.append(order)
        return olist

    def call(self, orderlist):
        assert isinstance(orderlist, list)
        # make BDAQ representation of orders from orderlist past
        self.req.Orders.Order = self.makeorderlist(orderlist)
        result = self.client.service.PlaceOrdersNoReceipt(self.req)
        allorders = bdaqapiparse.ParsePlaceOrdersNoReceipt(result, orderlist)
        if const.WRITEDB:
            self.dbman.WriteOrders(allorders, result.Timestamp)
        return allorders

# not fully implemented (do not use)
class APIPlaceOrdersWithReceipt(object):
    def __init__(self, apiclient, dbman):
        self.client = apiclient.client
        self.dbman = dbman
        self.createinput()

    def createinput(self):
        self.req = self.client.factory.create('PlaceOrdersWithReceiptRequest')
        # lets just do a single order at a time at the moment
        self.order = self.client.factory.create('SimpleOrderRequest')

    def makeorder(self, order):
        self.order._SelectionId = order.sid
        self.order._Stake = order.stake
        self.order._Price = order.price
        self.order._Polarity = order.polarity
        # we probably need to look at the market information to put
        # this stuff in correctly
        self.order._ExpectedSelectionResetCount = 1
        self.order. _ExpectedWithdrawalSequenceNumber = 0,         
        self.order._CancelOnInRunning = True
        self.order._CancelIfSelectionReset = True        

    def call(self, order):
        # order passed should be a dict with keys
        # see 'ordertest.py' for what the dict should contain
        self.makeorder(order)
        self.req.Orders.Order = [self.order]
        result = self.client.service.PlaceOrdersWithReceipt(self.req)
        return result

#class APIUpdateOrdersNoReceipt(object):

#class APICancelOrders(object):

#class APICancelAllOrdersOnMarket(object):

#class APICancelAllOrders(object):

class APIListBlacklistInformation(object):
    def __init__(self, apiclient):
        self.client = apiclient.client

    def call(self):
        result = self.client.service.ListBlacklistInformation()
        return result

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
