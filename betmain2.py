# betmain2.py
# James Mithen
# jamesmithen@gmail.com
#
# Main betting script.  Not currently implemented!!

import betman

class BetMain(object):
    def __init__(self, deltat):
        """deltat is time between price refreshes in seconds."""
        self.load_strategies()
        self.main_loop()
        self.clock = betman.all.clock.Clock(deltat)

    def loadstrategies(self):
        """Load strategies."""
        
        self.stratgroup = StrategyGroup()

        # add strategies here
        self.stratgroup.add(strat)

    def update_market_prices():
        """Get new prices and write to the database."""

    def main_loop(self):
        # will want to be able to break out of this loop somehow
        while True:
            self.clock.tick()

            # call BF and BDAQ API functions to get prices
            self.update_market_prices()

            # update the strategies: make/cancel bets etc.
            self.stratgroup.update()

        
        
