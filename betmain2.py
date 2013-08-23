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
        for m in msels:
            self.stratgroup.add(betman.strategy.mystrategy.\
                                CXStrategy(m[0], m[1]))

    def update_market_prices(self):
        """Get new prices and write to the database."""
        bdaqapi.GetSelections(self.marketids[const.BDAQID])
        bfapi.GetSelections(self.marketids[const.BFID])        

    def main_loop(self):
        # will want to be able to break out of this loop somehow
        #while True:
        for i in range(3):
            if const.DEBUG:
                print '-'*32
            
            # update the strategies: make/cancel bets etc.
            self.stratgroup.update()
            
            self.clock.tick()

            # call BF and BDAQ API functions to get prices
            self.update_market_prices()
        
#if __name__=='__main__':
bm = BetMain(30)
bm.main_loop()
