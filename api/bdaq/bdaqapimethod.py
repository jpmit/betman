import datetime
import time
from betman import const, util, Event, betlog
import bdaqapiparse
from betman.api.apimethod import ApiMethod

"""
Classes for calling the Betdaq Api Methods.  These are not designed to
be called from user applications directly; rather, use the interface
in bdaqapi.py by calling e.g. bdaqapi.ListTopLevelEvents().
"""

# classes that implement the read only methods, in the order that they
# appear in the Betdaq documentation 'NewExternalApispec.doc'.

class ApiListTopLevelEvents(ApiMethod):
    def __init__(self, apiclient):
        super(ApiListTopLevelEvents, self).__init__(apiclient)

    def create_req(self):
        self.req = self.client.factory.\
                   create('ListTopLevelEventsRequest')
        # this is the default, and I don't exactly know why we would
        # want True anyway, but lets set it just in case.
        self.req._WantPlayMarkets = False
        
    def call(self):
        """
        Return list of events. Note that there is no database table
        for events at the # moment, only for markets.
        """
        
        betlog.betlog.info('calling BDAQ Api ListTopLevelEvents')
        response = self.client.service.ListTopLevelEvents(self.req)
        events = bdaqapiparse.ParseListTopLevelEvents(response)
        return events
    
class ApiGetEventSubTreeNoSelections(ApiMethod):
    def __init__(self, apiclient, dbman):
        super(ApiGetEventSubTreeNoSelections,
              self).__init__(apiclient)
        self.dbman = dbman

    def create_req(self):
        self.req = self.client.factory.create(('GetEventSubTreeNoSele'
                                               'ctionsRequest'))
        # may want to change this sometime (?)
        self.req._WantPlayMarkets = False

    def call(self, ids, direct = False):
        """
        Return list of markets for events. ids should be a list of
        event ids e.g. calling with ids = [100004, 100005] will give
        all markets for 'Horse Racing' and 'Tennis'.
        """
        
        self.req.EventClassifierIds = ids
        self.req._WantDirectDescendentsOnly = direct
        self.req._WantPlayMarkets = False
        betlog.betlog.info('calling BDAQ Api GetEventSubTreeNoSelections')        
        response = self.client.service.\
                   GetEventSubTreeNoSelections(self.req)
        allmarkets = bdaqapiparse.\
                     ParseGetEventSubTreeNoSelections(response)

        if const.WRITEDB:
            self.dbman.write_markets(allmarkets, response.Timestamp)
        return allmarkets

# not fully implemented (do not use)
class ApiGetEventSubTreeWithSelections(ApiMethod):
    def __init__(self, apiclient):
        super(ApiGetEventSubTreeWithSelections,
              self).__init__(apiclient)

    def create_req(self):
        self.req = self.client.factory.\
                   create('GetEventSubTreeWithSelectionsRequest')
        # note that for this function (unlike NoSelections), can only
        # go down one level i.e. can only get 'direct descendants'
        self.req._WantPlayMarkets = False

    def call(self, ids):
        self.req.EventClassifierIds = ids
        result = self.client.service.\
                 GetEventSubTreeWithSelections(self.req)
        return result

class ApiGetMarketInformation(ApiMethod):
    def __init__(self, apiclient, dbman):
        super(ApiGetMarketInformation, self).__init__(apiclient)
        self.dbman = dbman

    def create_req(self):
        self.req = self.client.factory.\
                   create('GetMarketInformationRequest')

    def call(self, ids):
        """
        Return raw data of all market information.  Note that at the
        moment there is no 'MarketInfo' type class that contains this
        information.  Part of the reason for this is that this API
        function should not be required frequently.
        """

        self.req.MarketIds = ids
        betlog.betlog.info('calling BDAQ Api GetMarketInformation')
        result = self.client.service.GetMarketInformation(self.req)
        # note the raw data is returned here
        return result

# not fully implemented (do not use)
class ApiListSelectionsChangedSince(ApiMethod):
    def __init__(self, apiclient):
        super(ApiListSelectionsChangedSince, self).__init__(apiclient)

    def create_req(self):
        self.req = self.client.factory.\
                   create('ListSelectionsChangedSinceRequest')

    def call(self, seqnum):
        self.req._SelectionSequenceNumber = seqnum
        result = self.client.service.\
                 ListSelectionsChangedSince(self.req)
        return result

# not fully implemented (do not use)
class ApiListMarketWithdrawalHistory(ApiMethod):
    def __init__(self, apiclient):
        super(ApiListMarketWithdrawalHistory, self).__init__(apiclient)        

    def create_req(self):
        self.req = self.client.factory.create(('ListMarketWithdrawal'
                                               'HistoryRequest'))

    def call(self, ids):
        self.req.MarketId = ids
        result = self.client.service.\
                 ListMarketWithdrawalHistory(self.req)
        return result

class ApiGetPrices(ApiMethod):
    # maximum number of market ids we get get selection prices for in
    # a single API call (Set to 50 according to the API docs).
    MAXMIDS = 50 
    def __init__(self, apiclient, throttl = 0):
        super(ApiGetPrices, self).__init__(apiclient) 
        # time to wait between consecutive calls when calling multiple
        # times.
        self.throttl = throttl

    def create_req(self):
        self.req = self.client.factory.create('GetPricesRequest')
        self.req._ThresholdAmount = 0.0
        # set this to -1 for all prices, 0 for no prices, or a
        # positive number for a maximum number of prices.
        self.req._NumberForPricesRequired = const.NUMPRICES
        self.req._NumberAgainstPricesRequired = const.NUMPRICES
        self.req._WantMarketMatchedAmount = True
        self.req._WantSelectionsMatchedAmounts = True
        self.req._WantSelectionMatchedDetails = True

    def call(self, mids):
        """
        Return all selections for Market ids in mids, where mids is a
        list of market ids.
        """

        allselections = []
        # split up mids into groups of size MAXMIDS
        for (callnum, ids) in \
            enumerate(util.chunks(mids, ApiGetPrices.MAXMIDS)):
            self.req.MarketIds = ids
            if callnum > 0:
                # sleep for some time before calling Api again
                time.sleep(self.throttl)
                
            betlog.betlog.info('calling BDAQ Api GetPrices')
            result = self.client.service.GetPrices(self.req)
            selections =  bdaqapiparse.ParseGetPrices(ids, result)
            allselections = allselections + selections

        #if const.WRITEDB:
            # collapse list of lists to a flat list
        #    writeselections = [i for sub in allselections for i in sub]
        #    self.dbman.WriteSelections(writeselections, result.Timestamp)

        return allselections

# not fully implemented (do not use)
class ApiGetOddsLadder(ApiMethod):
    pass

# not fully implemented (do not use)
class ApiGetCurrentSelectionSequenceNumber(ApiMethod):
    def __init__(self, apiclient):
        super(ApiGetCurrentSelectionSequenceNumber,
              self).__init__(apiclient)         

    def call(self):
        result = self.client.service.\
                 GetCurrentSelectionSequenceNumber()
        return result

# classes that implement the secure methods, in the order that they 
# appear in the Betdaq documentation 'NewExternalApispec.doc'.

class ApiGetAccountBalances(ApiMethod):
    def __init__(self, apiclient, dbman):
        super(ApiGetAccountBalances, self).__init__(apiclient)
        self.dbman = dbman

    def create_req(self):
        pass

    def call(self):
        betlog.betlog.info('calling BDAQ Api GetAccountBalances')        
        result = self.client.service.GetAccountBalances()
        # accinfo is a dictionary of (_AvailableFunds, _Balance,
        # _Credit, _Exposure).
        accinfo = bdaqapiparse.ParseGetAccountBalances(result)
        if const.WRITEDB:
            self.dbman.write_account_balance(const.BDAQID, accinfo,
                                             result.Timestamp)

        return accinfo

# not fully implemented (do not use).  This one lists extra details
# about account, mainly orders settled between two dates.
class ApiListAccountPostings(ApiMethod):
    def __init__(self, apiclient):
        super(ApiListAccountPostings, self).__init__(apiclient)        

    def create_req(self):
        self.req = self.client.factory.\
                   create('ListAccountPostingsRequest')

    def call(self, *args):
        # should be able to pass two datetime ApiMethods here(?)
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

# class ApiListAccountPostingsById(ApiMethod):

# class ApiChangePassword(ApiMethod):

class ApiListOrdersChangedSince(ApiMethod):
    def __init__(self, apiclient, dbman):
        super(ApiListOrdersChangedSince, self).__init__(apiclient)        
        self.dbman = dbman

    def create_req(self):
        self.req = self.client.factory.\
                   create('ListOrdersChangedSinceRequest')

    def call(self, seqnum=None):
        global ORDER_SEQUENCE_NUMBER
        # the sequence number should come in the first instance from
        # the bootstrap, see class ApiListBootstrapOrders
        if seqnum:
            self.req.SequenceNumber = seqnum
        else:
            self.req.SequenceNumber = ORDER_SEQUENCE_NUMBER

        betlog.betlog.debug(('Calling ListOrdersChangedSince with '
                             'sequence number: {0}'\
                            .format(self.req.SequenceNumber)))
        
        resp = self.client.service.ListOrdersChangedSince(self.req)

        data = bdaqapiparse.ParseListOrdersChangedSince(resp)

        if not data:
            # should be returning an empty dict here, i.e. no orders
            # changed since last call.
            return data
        
        # if we did get some orders changed, the data consists of the
        # order information and the new max sequence number.
        orders, snum = data

        # set order sequence number to the maximum one returned by Api
        ORDER_SEQUENCE_NUMBER = snum        

        betlog.betlog.debug('Setting sequence number to: {0}'\
                            .format(snum))

        return orders

        # update changed orders
        #if const.WRITEDB:
        #    self.dbman.write_orders(orders.values(), resp.Timestamp)
        #return orders

# this sequence number is updated by both ApiListOrdersChangedSince
# (above) and ApiListBootstrapOrders (below).
ORDER_SEQUENCE_NUMBER = -1

class ApiListBootstrapOrders(ApiMethod):
    def __init__(self, apiclient, dbman):
        super(ApiListBootstrapOrders, self).__init__(apiclient)
        self.dbman = dbman

    def create_req(self):
        self.req = self.client.factory.\
                   create('ListBootstrapOrdersRequest')
        # this is probably the best default here (see BDAQ
        # documentation).
        self.req.wantSettledOrdersOnUnsettledMarkets = False

    def call(self, snum=-1):
        # the sequence number should come in the first instance from
        # the bootstrap which is next class
        global ORDER_SEQUENCE_NUMBER
        self.req.SequenceNumber = ORDER_SEQUENCE_NUMBER
        betlog.betlog.info('calling BDAQ Api ListBootstrapOrders')        
        result = self.client.service.ListBootstrapOrders(self.req)
        # assign sequence number we get back to ORDER_SEQUENCE_NUMBER
        ORDER_SEQUENCE_NUMBER = result._MaximumSequenceNumber
        allorders = bdaqapiparse.ParseListBootstrapOrders(result)
#        if const.WRITEDB:
#            self.dbman.write_orders(allorders.values(), result.Timestamp)
        return allorders

# not fully implemented (do not use)
class ApiGetOrderDetails(ApiMethod):
    def __init__(self, apiclient):
        super(ApiGetOrderDetails, self).__init__(apiclient)        

    def create_req(self):
        self.req = self.client.factory.create('GetOrderDetailsRequest')

    def call(self, oid):
        self.req._OrderId = oid
        result = self.client.service.GetOrderDetails(self.req)
        return result

class ApiPlaceOrdersNoReceipt(ApiMethod):

    # max number of orders that can be placed per API call
    MAXORDERS = 50

    def __init__(self, apiclient, dbman):
        super(ApiPlaceOrdersNoReceipt, self).__init__(apiclient)        
        self.dbman = dbman

    def create_req(self):
        self.req = self.client.factory.\
                   create('PlaceOrdersNoReceiptRequest')
        # if one fails, none will be placed
        self.req.WantAllOrNothingBehaviour = False

    def makeorderlist(self, orderlist):
        olist = []

        for o in orderlist:
            # make a single order ApiMethod
            order = self.client.factory.create('SimpleOrderRequest')

            order._SelectionId = o.sid
            order._Stake = o.stake
            order._Price = o.price
            order._Polarity = o.polarity
            # we probably need to look at the market information to put
            # this stuff in correctly
            order._ExpectedSelectionResetCount = o.src
            order. _ExpectedWithdrawalSequenceNumber = o.wsn,         
            order._CancelOnInRunning = o.cancelrunning
            order._CancelIfSelectionReset = o.cancelreset

            olist.append(order)
        return olist

    def call(self, orderlist):
        assert isinstance(orderlist, list)
        orders = {}
        for ol in util.chunks(orderlist, self.MAXORDERS):        
            # make BDAQ representation of orders from orderlist past
            self.req.Orders.Order = self.makeorderlist(ol)
            betlog.betlog.info('calling BDAQ Api PlaceOrdersNoReceipt')
            result = self.client.service.PlaceOrdersNoReceipt(self.req)
            ors = bdaqapiparse.ParsePlaceOrdersNoReceipt(result, orderlist)
            orders.update(ors)

        # note: could put result.Timestamp in order ApiMethod so that we
        # are saving the BDAQ time.
        return orders

# not fully implemented (do not use)
class ApiPlaceOrdersWithReceipt(ApiMethod):
    def __init__(self, apiclient, dbman):
        self.client = apiclient.client
        self.dbman = dbman
        self.create_req()

    def create_req(self):
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
        self.order._ExpectedWithdrawalSequenceNumber = 0
        self.order._CancelOnInRunning = True
        self.order._CancelIfSelectionReset = True 

    def call(self, order):
        # order passed should be a dict with keys
        # see 'ordertest.py' for what the dict should contain
        self.makeorder(order)
        self.req.Orders.Order = [self.order]
        betlog.betlog.info('calling BDAQ Api PlaceOrdersWithReceipt')
        result = self.client.service.PlaceOrdersWithReceipt(self.req)
        return result

class ApiUpdateOrdersNoReceipt(ApiMethod):
    # note, according to BDAQ API docs, we can't update an order on an
    # in-running market.  I guess instead we have to cancel the order
    # and make a new order at the new odds and/or stake.

    # max number of orders that can be updated per API call.
    MAXORDERS = 50

    def __init__(self, apiclient, dbman):
        super(ApiUpdateOrdersNoReceipt, self).__init__(apiclient)
        self.dbman = dbman
    
    def create_req(self):
        self.req = self.client.factory.create('UpdateOrdersNoReceiptRequest')

    def makeorderlist(self, orderlist):
        olist = []

        for o in orderlist:
            # add object for a single order update
            order = self.client.factory.create('UpdateOrdersNoReceiptRequestItem')

            order._BetId = o.oref
            order._DeltaStake = o.deltastake
            order._Price = o.price
            order._ExpectedSelectionResetCount = o.src
            order._ExpectedWithdrawalSequenceNumber = o.wsn
            order._CancelOnInRunning = o.cancelrunning
            order._CancelIfSelectionReset = o.cancelreset

            olist.append(order)
        return olist

    def call(self, orderlist):
        orders = {}
        for ol in util.chunks(orderlist, self.MAXORDERS):
            self.req.Orders.Order = self.makeorderlist(ol)
            betlog.betlog.info('calling BDAQ Api UpdateOrdersNoReceipt')
            result = self.client.service.UpdateOrdersNoReceipt(self.req)
            ors = bdaqapiparse.ParseUpdateOrdersNoReceipt(result, orderlist)
            orders.update(ors)

        return orders

class ApiCancelOrders(ApiMethod):
    def __init__(self, apiclient, dbman):
        super(ApiCancelOrders, self).__init__(apiclient)
        self.dbman = dbman

    def create_req(self):
        self.req = self.client.factory.create('CancelOrdersRequest')

    def call(self, olist):
        self.req.OrderHandle = [o.oref for o in olist]
        betlog.betlog.info('calling BDAQ Api CancelOrders')
        result = self.client.service.CancelOrders(self.req)
        odict = bdaqapiparse.ParseCancelOrders(result, olist)
        return odict

class ApiCancelAllOrdersOnMarket(ApiMethod):
    def __init__(self, apiclient, dbman):
        super(ApiCancelAllOrdersOnMarket, self).__init__(apiclient)
        self.dbman = dbman

    def create_req(self):
        self.req = self.client.factory.\
                   create('CancelAllOrdersOnMarketRequest')

    def call(self, midlist):
        self.req.MarketIds = midlist
        betlog.betlog.info('calling BDAQ Api CancelAllOrdersOnMarket')
        result = self.client.service.CancelAllOrdersOnMarket(self.req)
        ocancel = bdaqapiparse.ParseCancelAllOrdersOnMarket(result)
        return ocancel

class ApiCancelAllOrders(ApiMethod):
    # be careful with this method, since if there are too many orders
    # to be cancelled, we will get an error, response RC137 (see the
    # docs).
    def __init__(self, apiclient, dbman):
        super(ApiCancelAllOrders, self).__init__(apiclient)
        self.dbman = dbman

    def create_req(self):
        self.req = self.client.factory.\
                   create('CancelAllOrdersRequest')

    def call(self):
        betlog.betlog.info('calling BDAQ Api CancelAllOrders')
        result = self.client.service.CancelAllOrders(self.req)
        ocancel = bdaqapiparse.ParseCancelAllOrders(result)
        return ocancel

class ApiListBlacklistInformation(ApiMethod):
    def __init__(self, apiclient):
        super(ApiListBlacklistInformation, self).__init__(apiclient)

    def call(self):
        betlog.betlog.info('calling BDAQ Api ListBlacklistInformation')
        result = self.client.service.ListBlacklistInformation()
        return result

####################
# Suspending orders
####################

#class ApiSuspendFromTrading(ApiMethod):

#class ApiUnsuspendFromTrading(ApiMethod):

#class ApiSuspendOrders(ApiMethod):

#class ApiSuspendAllOrdersOnMarket(ApiMethod):

#class ApiSuspendAllOrders(ApiMethod):

#class ApiUnsuspendOrders(ApiMethod):

#####################
# Hearbeat stuff
# don't bother with all this for now
####################

#class ApiRegisterHeartbeat(ApiMethod):

#class ApiChangeHeartbeatRegistration(ApiMethod):

#class ApiDeregisterHeartbeat(ApiMethod):

#class ApiPulse(ApiMethod):
