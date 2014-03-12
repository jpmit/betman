"""Pricing and order manager.

The pricing manager gets pricing information from BDAQ / BF and pushes
the prices to the strategies that need it.

The order manager pulls order details from strategies, makes orders,
and keeps track of the status of orders so that the strategies can
pull the order status from the manager.

"""

import datetime
from betman import const, database, order, betlog
from betman.core import multi
from betman.api.bf import bfapi
from betman.api.bdaq import bdaqapi
from stores import OrderStore, PriceStore
from operator import attrgetter
import wx

# The following classes can be in an application as follows:

# (i) create a StrategyGroup, and for each strategy added set the
# attribute 'update_tick', which should be an integer. E.g. setting
# this to 1 will mean that new prices are fetched every tick, 5 will
# mean every 5 ticks, etc.

# (ii) create PricingManager, and call the tick method on each tick,
# which should probably be evenly spaced in time (e.g. by 1 second),
# but the length of time a tick corresponds to can be set by the
# application.

# (iii) call the update_if method on the strategy group, using
# attribute 'updated_last_tick' so that we only update the strategies
# that have new prices available.  This will perform AI/logic for the
# strategy and generate any new orders.
#
# (iv) call the get_new_orders method of the OrderManager to pull any
# new orders from the strategy group.
#
# The attributes used above can be changed by updating the constants
# UTICK and UPDATED below; these constants should be used in the
# application code.

UTICK = 'update_tick'
UPDATED = 'updated_last_tick'

# constant used for OrderManager only: to actually update order info,
# PRACTICEMODE must be set to False as well.
UPDATEORDERINFO = True

class OrderManager(object):
    def __init__(self, stratgroup, config):

        # group of all existing strategies
        self.stratgroup = stratgroup

        # app config - we may be in 'practice mode', in which case we
        # don't want to place any bets.
        self.gconf = config

        # order model stores everything to do with orders made since
        # the start of the application.  It also writes any
        # information to the database as required.
        self.ostore = OrderStore.Instance()

        # we do store a ref to current order dictionary
        #self.orders = self.ostore._orders

        # call startup routine to bootstap BDAQ order information, and
        # login to betfair.
        self.bootstrap()

    def bootstrap(self):
        # bootstrap BDAQ order information (we don't need to do this
        # for BF).  We don't need to save these orders (?).
        ords = bdaqapi.ListBootstrapOrders()
        while ords:
            ords = bdaqapi.ListBootstrapOrders()

        # login to BF api (we don't need to do this for BF).  Note if
        # we are not configured to login to BF on startup, we will
        # need to Login at some point later, otherwise we will get API
        # errors when trying to make / update orders.
        if self.gconf.BFLogin:
            bfapi.Login()

    def get_new_orders(self):
        """Get new order dictionary from the strategy group."""

        # note we only get orders from the strategies with UPDATED =
        # True, i.e. only those which got new pricing information this
        # tick.  Among other reasons, this is because some strategies
        # (e.g. MMStrategy) need to be fed new prices in order to
        # clear the order dictionary, so if we didn't use _if, we
        # could potentially place these orders many times.

        return self.stratgroup.get_orders_to_place_if(UPDATED)

    def get_cancel_orders(self):
        """Get cancel order dictionary from the strategy group."""

        return self.stratgroup.get_orders_to_cancel_if(UPDATED)

    def get_update_orders(self):
        """Get update order dictionary from the strategy group."""

        return self.stratgroup.get_orders_to_update_if(UPDATED)

    def make_orders(self):
        """Use BDAQ/BF Apis to cancel, update, and make new orders"""

        # orders to cancel from all of the strategies
        ocancel = self.get_cancel_orders()

        # orders to update from all of the strategies
        oupdate = self.get_update_orders()

        # new orders from all of the strategies
        onew = self.get_new_orders()
        
        # do we need to cancel, update, or make new orders?
        tocancel = bool(ocancel[const.BDAQID] or ocancel[const.BFID])
        toupdate = bool(oupdate[const.BDAQID] or oupdate[const.BFID])
        tonew = bool(onew[const.BDAQID] or onew[const.BFID])

        if tocancel:
            betlog.betlog.debug('cancelling orders: {0}'.format(ocancel))

        if toupdate:
            betlog.betlog.debug('updating orders: {0}'.format(oupdate))

        if tonew:
            betlog.betlog.debug('making new orders: {0}'.format(onew))

        if (tocancel or toupdate or tonew):
            
            # we could instead do 'monkey patching' here so we don't
            # need to check this every tick...
            if self.gconf.PracticeMode:
                # we don't make any real money bets in practice mode
                print 'bets not made since in practice mode'
                return

            # call multithreaded make orders so that we make all order
            # requests (cancelling, updating, making new) for BDAQ and
            # BF simultaneously.
            corders, uorders, neworders = multi.\
                                          make_orders(ocancel, oupdate, onew)

            # save the full order information to the order store (this will
            # handle writing to the DB, etc.)
            self.ostore.add_orders(corders, uorders, neworders)

        else:
            
            # we need to set latest cancel, update, new orders to be
            # empty.
            self.ostore.latest = [{const.BDAQID: {}, const.BFID: {}}, 
                                  {const.BDAQID: {}, const.BFID: {}}, 
                                  {const.BDAQID: {}, const.BFID: {}}]

    def update_order_information(self):

        if self.gconf.PracticeMode or (not UPDATEORDERINFO):
            return

        # if we don't have any strategies, don't update.  We might
        # want to change this at some point, but doing anything
        # different from this is a little complicated.
        if not self.stratgroup.strategies:
            return

        # get list of unmatched orders on BDAQ
        bdaqunmatched = self.ostore.get_unmatched_orders(const.BDAQID)
            
        # get list of unmatched orders on BF
        bfunmatched = self.ostore.get_unmatched_orders(const.BFID)

        # only want to call BDAQ API if we have unmatched bets
        if bdaqunmatched:
            # this should automatically keep track of a 'sequence
            # number', so that we are updating information about all
            # orders.
            bdaqors = bdaqapi.ListOrdersChangedSince()
            # debug
            for o in bdaqors.values():
                print o.__dict__
        else:
            bdaqors = {}
        self.ostore.process_order_updates(const.BDAQID, bdaqors, 
                                          bdaqunmatched)

        if bfunmatched:
            # we pass this function the list of order objects;
            bfors = bfapi.GetBetStatus(bfunmatched)
        else:
            bfors = {}
        self.ostore.process_order_updates(const.BFID, bfors, 
                                          bfunmatched)

class PricingManager(object):
    def __init__(self, stratgroup):

        self.stratgroup = stratgroup

        # the price store actually holds the data
        self.pstore = PriceStore.Instance()

        # current prices
        #self.prices = {const.BDAQID: {}, const.BFID: {}}

        # same as above but only contains mids that were updated in
        # the last tick.
        #self.new_prices = {const.BDAQID: {}, const.BFID: {}}

    def get_strategy_with_mid(bdaqmid):
        """
        Return strategy with given bdaqmid.  If multiple strategies
        have this bdaqmid, return the strategy with the smallest UTICK
        value.  If no strategy exists, return None.
        """

        strats = []

        for strat in self.stratgroup.strategies:
            if bdaqmid in strat.get_marketids()[const.BDAQID]:
                strats.append(strat)

        # sort according to utick attribute
        strats.sort(key = attrgetter(UTICK))

        if strats:
            return strats[0]
        return None
    
    def update_prices(self, ticks):
        """Update the pricing dictionary."""

        # dictionary of mids (market ids) to update
        update_mids = {const.BDAQID: [], const.BFID: []}

        print len(self.stratgroup), 'strategies to update'

        # figure out which strategies in the stratgroup need new
        # prices this tick, and add their mids to update_mids.
        for strat in self.stratgroup:
            if (ticks % getattr(strat, UTICK) == 0):
                # add the mids used by the strategy to the list of
                # mids to update.
                mids = strat.get_marketids()

                # note we may only have BDAQ mids or BF mids
                update_mids[const.BDAQID] += mids.get(const.BDAQID, [])
                update_mids[const.BFID] += mids.get(const.BFID, [])

                # set flag on strategy to indicate that we were
                # updated on the last tick.
                setattr(strat, UPDATED, True)
            else:
                setattr(strat, UPDATED, False)

        # remove duplicate mids
        if const.BDAQID in update_mids:
            update_mids[const.BDAQID] = list(set(update_mids[const.BDAQID]))
        if const.BFID in update_mids:
            update_mids[const.BFID] = list(set(update_mids[const.BFID]))

        if update_mids[const.BDAQID] or update_mids[const.BFID]:
            print 'updating mids', update_mids

        # call BDAQ and BF API
        new_prices, emids = multi.update_prices(update_mids)

        # remove any strategies from the strategy list that depend on
        # any of the BDAQ or BF markets in emids.
        for myid in [const.BDAQID, const.BFID]:
            if emids.get(myid):
                self.stratgroup.remove_marketids(myid, emids[myid])

        # add the new prices to the price store
        self.pstore.add_prices(new_prices)
