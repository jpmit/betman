# mmstrategy.py
# James Mithen
# jamesmithen@gmail.com

"""Market making strategy for both exchanges simultaneously."""

from betman import const, order
from betman.strategy import strategy, mmstrategy

class BothMMStrategy(strategy.Strategy):
    """Market making strategy for a single selection.

    This will make the market on both BDAQ and BF.  To do this, we
    simply encapsulate two MMStrategy objects in this class.
    """

    def __init__(self, sel1, sel2):
        """Create the single exchange MM strategies."""

        super(BothMMStrategy, self).__init__()
        
        # sel1 and sel2 can be either exchange, but usually sel1 with
        # be BDAQ and sel2 BF.
        self.strat1 = mmstrategy.MMStrategy(sel1)
        self.strat2 = mmstrategy.MMStrategy(sel2)

        # overload certain functionality of self.brain.  The above
        # super() call gives us self.brain, but really we are using
        # self.strat1.brain and self.strat2.brain to do the reasoning.
        # Since the monitorframe accesses information of self.brain
        vs = lambda : self.strat1.brain.get_visited_states() + self.strat2.brain.get_visited_states()
        nvs = lambda : self.strat1.brain.get_num_visited_states() + self.strat2.brain.get_num_visited_states()
        self.brain.get_visited_states = vs
        self.brain.get_num_visited_states = nvs

    def get_marketids(self):
        mids1 = self.strat1.get_marketids()
        mids2 = self.strat2.get_marketids()
        allids = {const.BDAQID: [], const.BFID: []}
        for k in [const.BDAQID, const.BFID]:
            allids[k] = mids1.get(k, []) + mids2.get(k, []) 
        return allids
        
    def get_orders_to_place(self):
        pl1 = self.strat1.get_orders_to_place()
        pl2 = self.strat2.get_orders_to_place()
        allpl = {const.BDAQID: [], const.BFID: []}
        for k in [const.BDAQID, const.BFID]:
            allpl[k] = pl1.get(k, []) + pl2.get(k, []) 
        return allpl

    def update_prices(self, prices):
        """Update price info (from API) for both strategies."""
        
        self.strat1.update_prices(prices)
        self.strat2.update_prices(prices)
        
    def update_orders(self, orders):
        """Update order info (from API) for both strategies."""

        self.strat1.update_orders(orders)
        self.strat2.update_orders(orders)

    def get_allorders(self):
        # we may want to order these according to time placed at some
        # point
        return self.strat1.get_allorders() + self.strat2.get_allorders()
