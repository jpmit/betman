# mystrategy.py
# James Mithen
# jamesmithen@gmail.com

# actual strategies.  These inherit from the base classes in
# strategy.py.

import strategy

# commission on winnings taken from both exchanges. The strategies can
# easily be generalised to the case when the commissions for BDAQ and
# BF are different.
_COMMISSION = 0.05

# Default size lay bet
_DEFAULTLAY = 0.5
# Default size back bet (we will have to change this to be correct)
_DEFAULTBACK = 0.01

class CXStrategy(strategy.Strategy):
    """Cross exchange strategy"""
    def __init__(self, ex1sel, ex2sel):
        super(CXStrategy, self).__init__()
        self.sel1 = ex1sel
        self.sel2 = ex2sel

        # add states
        noopp_state = CXStateNoOpp(self)
        self.brain.add_state(noopp_state)
   
    def check_opportunity(self):
        """Can I offer a better back than currently available, and then
        back on the other exchange at the current price?"""
        self.opp = False

        for s1,s2 in [(self.sel1,self.sel2), (self.sel2,self.sel1)]:
            # lay selection at best current price
            olay = s1.make_best_back()

            # back selection at best current price
            oback = s2.best_back()

            if self._backlay(oback, olay):
                self.store_opportunity(s1, s2, olay, oback)
                return True
        return False

    def check_instant_opportunity(self):
        """Can I back on one exchange and lay on the other exchange at
        prices that are currently on offer?"""
        self.opp = False

        for s1,s2 in [(self.sel1,self.sel2), (self.sel2,self.sel1)]:
            # lay selection at best current price
            olay = s1.best_lay()
            if olay == 1.0:
                # no lay price is currently offered
                return False

            # back selection at best current price
            oback = s2.best_back()

            if self._backlay(oback, olay):
                self.store_opportunity(s1, s2, olay, oback, True)
                return True
        return False


    def store_opportunity(self, slay, sback, olay, oback,
                          instant = False):
        """Store details of betting opportunity"""
        self.opp = True
        self.slay = slay
        self.sback = sback
        self.olay = olay
        self.oback = oback
        self.instant = False
        
        # create both back and lay orders
        self.border = order.PlaceOrder(sback.exid, sback.id, _DEFAULTBACK,
                                       self.oback, 1)
        self.lorder = order.PlaceOrder(slay.exid, slay.id, _DEFAULTLAY,
                                       self.olay, 2)        

class MMStrategy(strategy.Strategy):
    """Market making strategy"""
    def __init__(self):
        super(CXStrategy, self).__init__()

class CXStateOpp(strategy.State):
    """An opportunity"""
    def __init__(self, cxstrat):
        super(CXStateNoOpp, self).__init__('opp')
        self.cxstrat = cxstrat

class CXStateInstantOpp(strategy.State):
    """An instant opportunity"""
    def __init__(self, cxstrat):
        super(CXStateNoOpp, self).__init__('instantopp')
        self.cxstrat = cxstrat

    def entry_actions(self):
        # place both bets - back and lay simultaneously!

        # change state again
        self.cxstrat.brain.set_state('bothplaced')
        self.cxstrat.brain.active_state.entry_actions()

class CXStateOpp(strategy.State):
    """An opportunity"""
    def __init__(self, cxstrat):
        super(CXStateNoOpp, self).__init__('opp')
        self.cxstrat = cxstrat

    def entry_actions(self):
        # place lay bet

    def do_actions(self):
        # we should have placed a bet already, so need to
        # 1. check that the bet has been accepted
        # 2. if so, put on the lay bet
        # 3. if not, are we still the best lay?
        # 4. if we are not still the best lay, can we move to be the best lay
        #    and make the strategy viable? (if so alter the lay bet)
        
class CXStateNoOpp(strategy.State):
    """No betting opportunity"""
    def __init__(self, cxstrat):
        super(CXStateNoOpp, self).__init__('noopp')
        self.cxstrat = cxstrat

    def do_actions(self):
        # refresh prices from database

    def check_conditions(self):
        # check if there is an instant opportunity
        if self.check_instant_opportunity():
            return 'instantopp'
        elif self.check_opportunity():
            return 'opp'
        # if no opportunities, don't change state
        return None
