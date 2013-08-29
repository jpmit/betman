# betmain2.py
# James Mithen
# jamesmithen@gmail.com
#
# Main betting script.

import betman
from betman import const
from betman.api.bf import bfapi
from betman.api.bdaq import bdaqapi

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

    def load_strategies(self):
        """Load strategies."""
        
        self.stratgroup = betman.strategy.strategy.StrategyGroup()

        # add strategies here
        msels = betman.database.DBMaster().ReturnSelectionMatches()
        if const.DEBUG:
            print "Found {0} strategies".format(len(msels))
        # alter the prices so that we get instant opp!!
        msels[0][0].backprices[0] = (1.50, 10)
        msels[0][1].layprices[0] = (1.01, 10)        
        for m in msels[:50]:
            self.stratgroup.add(betman.strategy.mystrategy.\
                                CXStrategy(m[0], m[1]))

    def update_market_prices(self):
        """Get new prices and write to the database."""
        bdaqapi.GetSelections(self.marketids[const.BDAQID])
        bfapi.GetSelections(self.marketids[const.BFID])

    def update_order_information(self):
        """Get information on all current orders."""
        odict = self.stratgroup.get_orderids()        

    def make_orders(self):
        """Make outstanding orders for all strategies"""
        # get dictionary of outstanding orders for all strategies.
        # Keys are const.BDAQID and const.BFID
        odict = self.stratgroup.get_orders_to_place()
        print odict

        if not const.PRACTICEMODE:
            bdaqapi.APIPlaceOrdersNoReceipt(odict[const.BDAQID])
            bfapi.APIPlaceOrders(odict[const.BFID])

    def main_loop(self):
        # will want to be able to break out of this loop somehow
        #while True:
        for i in range(3):
            if const.DEBUG:
                print '-'*32
            
            # update the strategies: refresh prices of any selections
            # from DB - these will have come from
            # update_market_prices, do the AI, and create any orders.
            self.stratgroup.update()

            # make any outstanding orders.
            self.make_orders()
            
            self.clock.tick()

            # call BF and BDAQ API functions to get prices and update order information
            self.update_market_prices()
            self.update_order_information()
        
#if __name__=='__main__':
bm = BetMain(30)
#bm.main_loop()
