# mmstrategy.py
# James Mithen
# jamesmithen@gmail.com

"""Market making strategy."""

from betman import const, order
from betman.strategy import strategy

# commission on winnings taken from both exchanges.
_COMMISSION = {const.BDAQID: 0.05, const.BFID: 0.05}

# min bets on each exchange in GBP.  Note we can be clever placing
# bets on BF, we can have minimum bet of 0.01 on BF!
_MINBETS = {const.BDAQID: 0.5, const.BFID: 2.0}

# small number used for fp arithmetic
_EPS = 0.000001

class MMStrategy(strategy.Strategy):
    """Market making strategy for a single selection."""
    
    def __init__(self, sel = None):
        """
        sel - selection (either BDAQ or BF).
        """
        
        super(MMStrategy, self).__init__()

        self.sel = sel

        # add states
        noopp_state = MMStateNoOpp(self)
        opp_state = MMStateOpp(self)        
        both_placed_state = MMStateBothPlaced(self)
        back_matched_state = MMStateBackMatched(self)
        lay_matched_state = MMStateLayMatched(self)
        both_matched_state = MMStateBothMatched(self)

        self.brain.add_state(noopp_state)
        self.brain.add_state(opp_state)
        self.brain.add_state(both_placed_state)
        self.brain.add_state(back_matched_state)        
        self.brain.add_state(lay_matched_state)
        self.brain.add_state(both_matched_state)        

        # initialise into noopp state
        self.brain.set_state(noopp_state.name)

    def __str__(self):
        return '{0} ({1})'.format(self.sel.name, self.sel.exid)

    def get_marketids(self):
        return {self.sel.exid: [self.sel.mid]}

    def update(self, prices):
      
        # important: clear the list of orders to be placed so that we
        # don't place them again.
        self.toplace = {const.BDAQID: [], const.BFID: []}

        # update selection price
        self.sel = prices[self.sel.exid][self.sel.mid][self.sel.id]

        # TODO: update status of any orders...

        # AI
        self.brain.update()

    def can_make(self):
        """Return True if we 'can' make a market here"""

        # At the moment, we will say we can make a market if we can
        # make both best back and best lay and be the only person
        # there.
        if self.sel.make_best_lay() > self.sel.make_best_back() + _EPS:
            return True
        return False

    def create_orders(self):
        """Create both back and lay orders."""

        # 1 pound at the moment
        bstake, lstake = 1.0, 1.0

        oback = self.sel.make_best_lay()
        olay = self.sel.make_best_back()

        sel = self.sel
        
        self.border = order.Order(sel.exid, sel.id, bstake,
                                  oback, 1, **{'mid': sel.mid,
                                               'src': sel.src,
                                               'wsn': sel.wsn,
                                               'sname': sel.name})
        self.lorder = order.Order(sel.exid, sel.id, lstake,
                                  olay, 2, **{'mid': sel.mid,
                                              'src': sel.src,
                                              'wsn': sel.wsn,
                                              'sname': sel.name})

class MMStateNoOpp(strategy.State):
    """No betting opportunity."""

    def __init__(self, mmstrat):
        super(MMStateNoOpp, self).__init__('noopp')
        self.mmstrat = mmstrat

    def do_actions(self):
        # refresh prices from database
        pass

    def check_conditions(self):
        # check if there is an opportunity to make the market.
        if self.mmstrat.can_make():
            # create the back and lay orders
            self.mmstrat.create_orders()
            return 'opp'
        
        # if no opportunities, don't change state
        return None

class MMStateOpp(strategy.State):
    """An opportunity to make the market."""

    def __init__(self, mmstrat):
        super(MMStateOpp, self).__init__('opp')
        self.mmstrat = mmstrat

    def entry_actions(self):
        # place both bets on the to be placed list
        self.mmstrat.toplace[self.mmstrat.sel.exid] = [self.mmstrat.border,
                                                       self.mmstrat.lorder]

        # change state again
        self.mmstrat.brain.set_state('bothplaced')

    def do_actions(self):
        pass

    def check_conditions(self):
        # check if there is an opportunity to make the market.
        if self.mmstrat.can_make():
            return 'opp'
        
        # if no opportunities, don't change state
        return None

# TODO: all of the states below!
class MMStateBothPlaced(strategy.State):
    def __init__(self, mmstrat):
        super(MMStateBothPlaced, self).__init__('bothplaced')
        self.mmstrat = mmstrat

# we won't reach any of these states (yet)
class MMStateBackMatched(strategy.State):
    def __init__(self, mmstrat):
        super(MMStateBackMatched, self).__init__('backmatched')
        self.mmstrat = mmstrat

class MMStateLayMatched(strategy.State):
    def __init__(self, mmstrat):
        super(MMStateLayMatched, self).__init__('laymatched')
        self.mmstrat = mmstrat

class MMStateBothMatched(strategy.State):
    def __init__(self, mmstrat):
        super(MMStateBothMatched, self).__init__('bothmatched')
        self.mmstrat = mmstrat
