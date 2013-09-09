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

# in practicemode, we won't place any bets
PRACTICEMODE = False

# can choose whether or not to use BDAQ API for prices (we don't use
# the BF API automatically).
USEBDAQAPI = False

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
        
        self.stratgroup = betman.strategy.strategy.StrategyGroup()

        # add strategies here
        msels = betman.database.DBMaster().ReturnSelectionMatches()

        betlog.betlog.debug("Found {0} strategies".format(len(msels)))
        # alter the prices so that we get instant opp!!
        msels[0][0].backprices[0] = (1.50, 10)
        msels[0][1].layprices[0] = (1.01, 10)        
        for m in msels[:100]:
            self.stratgroup.add(betman.strategy.mystrategy.\
                                CXStrategy(m[0], m[1]))

    def update_market_prices(self):
        """Get new prices and write to the database."""
        if USEBDAQAPI:
            bdaqapi.GetSelections(self.marketids[const.BDAQID])
        else:
            bdaqapi.GetSelectionsnonAPI(self.marketids[const.BDAQID])

            
        bfapi.GetSelections(self.marketids[const.BFID])

    def update_order_information(self):
        """Get information on all current orders."""
        odict = self.stratgroup.get_orders()

        if not PRACTICEMODE:
            # this should automatically keep track of a 'sequence
            # number', so that we are updating information about all
            # orders
            bdaqapi.ListOrdersChangedSince()
            # check we actually have some BF orders under
            # consideration.
            if odict[const.BFID]:
                bfapi.GetBetStatus(odict[const.BFID])

    def make_orders(self):
        """Make outstanding orders for all strategies"""
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
    bm = BetMain(20)
    bm.main_loop()
