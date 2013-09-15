# betmain2.py
# James Mithen
# jamesmithen@gmail.com
#
# Main betting program.

import time
import betman
from betman import const
from betman.api.bf import bfapi
from betman.api.bdaq import bdaqapi
from betman.all import betlog
import betutil
from multiprocessing.pool import ThreadPool

# in practicemode, we won't place any bets
PRACTICEMODE = True

# if this is set to false, we won't update any order info
UPDATEORDERINFO = False

class BetMain(object):
    def __init__(self, deltat):
        """deltat is time between price refreshes in seconds."""
        
        self.load_strategies()
        
        # market ids for all strategies (for updating prices)
        self.marketids = self.stratgroup.get_marketids()
        self.clock = betman.all.clock.Clock(deltat)
        
        # here we store a list of orders for both exchanges.  Only the
        # orders that are not yet matched are stored.
        self.orderdict = {const.BDAQID: [], const.BFID: []}

        # call the API functions to refresh prices etc.
        self.on_startup()

    def load_strategies(self):
        """Load strategies."""

        # load from pickle file
        try:
            sgroup = betutil.unpickle_stratgroup()
        except IOError:
            betlog.betlog.warn(('Could not read pickle file: attempting'
                                ' to read strategies from database'))
            # save strategies from DB to pickle file
            betutil.save_strategies()

            # load from the pickle file
            sgroup = betutil.unpickle_stratgroup()

        betlog.betlog.debug("Loaded {0} strategies".format(len(sgroup)))
        self.stratgroup = sgroup


    def update_market_prices(self):
        """
        Get new prices and write to the database.  Here we use
        python's threading module to make the requests to BDAQ and BF
        (approximately) simultaneously.
        """

        betlog.betlog.debug('Updating prices for {0} strategies'\
                            .format(len(self.stratgroup)))
        
        # market ids for all strategies (for updating prices)
        self.marketids = self.stratgroup.get_marketids()

        betlog.betlog.debug('BDAQ market ids total: {0}'.\
                            format(len(self.marketids[const.BDAQID])))
        
        betlog.betlog.debug('BF market ids total: {0}'.\
                            format(len(self.marketids[const.BFID])))

        pool = ThreadPool(processes=1)

        # update prices from BDAQ API.
        async_result = pool.apply_async(bdaqapi.GetSelectionsnonAPI,
                                        (self.marketids[const.BDAQID],))

        # update prices from BF API. Note at the moment there doesn't
        # seem to be a problem with requesting data for markets that
        # have closed, but we may have to change this at a later date.
        bfsels, bfemids = bfapi.GetSelections(self.marketids[const.BFID])

        bdaqsels, bdaqemids = async_result.get()

        # remove any strategies from the strategy list that depend on
        # any of the BDAQ or BF markets in emids.
        if bdaqemids:
            self.stratgroup.remove_marketids(const.BDAQID, bdaqemids)
            self.marketids = self.stratgroup.get_marketids()
        
        if bfemids:
            self.stratgroup.remove_marketids(const.BFID, bfemids)
            self.marketids = self.stratgroup.get_marketids()

        # if we deleted any strategies, re-save the pickle so we only
        # load valid strategies at startup
        if bdaqemids or bfemids:
            betutil.pickle_stratgroup(self.stratgroup)

    def update_order_information(self):
        """Get information on all current orders."""
        odict = self.stratgroup.get_orders()

        if (not PRACTICEMODE) and (UPDATEORDERINFO):
            # this should automatically keep track of a 'sequence
            # number', so that we are updating information about all
            # orders.
            bdaqapi.ListOrdersChangedSince()
            
            # check we actually have some BF orders under
            # consideration.
            if odict[const.BFID]:
                bfapi.GetBetStatus(odict[const.BFID])

    def make_orders(self):
        """Make outstanding orders for all strategies."""
        # get dictionary of outstanding orders for all strategies.
        # Keys are const.BDAQID and const.BFID
        odict = self.stratgroup.get_orders_to_place()
        betlog.betlog.debug('making orders: {0}'.format(odict))

        if not PRACTICEMODE:
            # are there any BDAQ orders pending?
            if odict[const.BDAQID]:
                # place the orders
                bdaqapi.PlaceOrders(odict[const.BDAQID])
            
            # Annoying!  The BF API only allows us to make bets for
            # one market at a time (although we can make multiple bets
            # - up to 60 apparently - for each market.
            if odict[const.BFID]:
                for plorder in odict[const.BFID]:
                    bfapi.PlaceBets([plorder])

    def on_startup(self):
        # put all this stuff in __init__ eventually??
        
        # bootstrap BDAQ order information (we don't need to do this
        # for BF).
        ords = bdaqapi.ListBootstrapOrders()
        while ords:
            ords = bdaqapi.ListBootstrapOrders()

        # need to login to BF api (we don't need to do this for BF).
        bfapi.Login()

        #  update market prices
        self.update_market_prices()

    def main_loop(self):

        # first tick initializes clock
        self.clock.tick()
        while True:
            # print intro stuff
            print time.asctime()
            print '-'*32
            
            # update the strategies: refresh prices of any selections
            # from DB - these will have come from
            # update_market_prices, do the AI, and create any orders.
            self.stratgroup.update()

            # make any outstanding orders.
            self.make_orders()
            
            self.clock.tick()

            # call BF and BDAQ API functions to get prices and update
            # order information
            self.update_market_prices()
            self.update_order_information()
        
if __name__=='__main__':
    bm = BetMain(2)
    bm.main_loop()
