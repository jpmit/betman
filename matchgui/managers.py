"""
Pricing and order manager.

The pricing manager gets pricing information from BDAQ / BF and pushes
the prices to the strategies that need it.

The order manager pulls order details from strategies, and makes
orders, and keeps track of the status of orders so that the strategies
can pull the order status from the manager.
"""

from betman import const, multi
from operator import attrgetter

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

class OrderManager(object):
    def __init__(self, stratgroup):
        self.stratgroup = stratgroup
        self.orders_to_place = {const.BDAQID: [], const.BFID: []}

    def get_new_orders(self):
        """Get new orders from the strategy group."""

        # note we get orders from all the strategies, not just those
        # with UPDATED = True.  But those with UPDATED = False will
        # return a blank order dictionary.

        self.orders_to_place = self.stratgroup.get_orders_to_place()

    def make_orders(self):
        pass

    def update_order_information(self):
        pass

class PricingManager(object):
    def __init__(self, stratgroup):

        self.stratgroup = stratgroup

        # current prices
        self.prices = {const.BDAQID: {}, const.BFID: {}}

        # same as above but only contains mids that were updated in
        # the last tick.
        self.new_prices = {const.BDAQID: {}, const.BFID: {}}

        # counter to store how many times we have ticked
        self.ticks = 0

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
    
    def update_prices(self):
        """Update the pricing dictionary."""

        self.ticks += 1

        # dictionary of mids (market ids) to update
        update_mids = {const.BDAQID: [], const.BFID: []}

        print len(self.stratgroup), 'strategies to update'

        # figure out which strategies in the stratgroup need new
        # prices this tick, and add their mids to update_mids.
        for strat in self.stratgroup:
            print getattr(strat, UTICK), self.ticks
            if (self.ticks % getattr(strat, UTICK) == 0):
                # add the mids used by the strategy to the list of
                # mids to update.
                print 'found a strat... getting mids'
                mids = strat.get_marketids()
                update_mids[const.BDAQID] += mids[const.BDAQID]
                update_mids[const.BFID] += mids[const.BFID]

                # set flag on strategy to indicate that we were
                # updated on the last tick.
                setattr(strat, UPDATED, True)
            else:
                setattr(strat, UPDATED, False)

        print 'updating mids', update_mids

        # call BDAQ and BF API
        self.new_prices, emids = multi.update_prices(update_mids)

        # remove any strategies from the strategy list that depend on
        # any of the BDAQ or BF markets in emids.
        for myid in [const.BDAQID, const.BFID]:
            if emids[myid]:
                self.stratgroup.remove_marketids(myid, emids[myid])

        # merge the new prices dict into self.prices
        self.prices.update(self.new_prices)
