# mystrategy.py
# James Mithen
# jamesmithen@gmail.com

# actual strategies.  These inherit from the base classes in
# strategy.py.

import strategy
from betman import const, database
from betman.all import order
from betman.api.bdaq import bdaqapi

# commission on winnings taken from both exchanges. The strategies can
# easily be generalised to the case when the commissions for BDAQ and
# BF are different.
_COMMISSION = {const.BDAQID: 0.05, const.BFID: 0.05}

# min bets on each exchange in GBP.  Note once we have improved
# placing bets on BF, we can have minimum bet of 0.01 on BF!
_MINBETS = {const.BDAQID: 0.5, const.BFID: 2.0}

class CXStrategy(strategy.Strategy):
    """
    Cross exchange strategy
    ex1sel - Selection object for exchange 1 (BetDaq)
    ex2sel - Selection object for exchange 2 (BetDaq)
    """
    def __init__(self, ex1sel, ex2sel):
        # this gives us self.brain, a StateMachine, and self.toplace,
        # a dictionary of orders waiting to be placed (see
        # strategy.py).
        super(CXStrategy, self).__init__()
        self.sel1 = ex1sel
        self.sel2 = ex2sel

        # database interface
        self.dbman = database.DBMaster()

        # add states
        noopp_state = CXStateNoOpp(self)
        instantopp_state = CXStateInstantOpp(self)        
        opp_state = CXStateOpp(self)
        lay_placed_state = CXStateLayPlaced(self)        
        back_placed_state = CXStateLayPlaced(self)                
        both_placed_state = CXStateBothPlaced(self)
        lay_matched_state = CXStateLayMatched(self)
        back_matched_state = CXStateBackMatched(self)
        both_matched_state = CXStateBothMatched(self)
        
        self.brain.add_state(noopp_state)
        self.brain.add_state(instantopp_state)        
        self.brain.add_state(opp_state)
        self.brain.add_state(lay_placed_state)
        self.brain.add_state(back_placed_state)        
        self.brain.add_state(both_placed_state)
        self.brain.add_state(lay_matched_state)
        self.brain.add_state(back_matched_state)
        self.brain.add_state(both_matched_state)        

        # initialise into noopp state
        self.brain.set_state(noopp_state.name)

    def get_marketids(self):
        """Return dictionary of all market ids involved in strategy."""
        return {const.BDAQID: [self.sel1.mid],
                const.BFID: [self.sel2.mid]}

    def get_orders(self):
        """Return dictionary of all order objects involved in
        strategy.  This is needed so that we can check the status of
        the orders (we only in fact really need this for the BF
        orders)"""
        odict = {const.BDAQID: [], const.BFID: []}
        # note: we only care about checking the order status if we
        # don't know for sure whether or not it is matched. We also
        # only care about the order if it has been placed, in fact we
        # need it to have been placed in order to update its status.
        if hasattr(self, 'border'):
            if self.border.status != order.MATCHED and self.border.status != order.NOTPLACED:
                odict[self.border.exid].append(self.border)
        if hasattr(self, 'lorder'):
            if self.lorder.status != order.MATCHED and self.lorder.status != order.NOTPLACED:
                odict[self.lorder.exid].append(self.lorder)
        return odict
        
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
                # TODO: the odds are good enough, we just need to check if
                # the volume is there.
                #bstake, lstake = 
                self.store_opportunity(s1, s2, olay, oback, True)
                return True
        return False
   
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

    def store_opportunity(self, slay, sback, olay, oback):
        """Store details of betting opportunity"""
        self.opp = True
        self.slay = slay
        self.sback = sback
        self.olay = olay
        self.oback = oback
        self.instant = False
        # Figure out how much we want to back and how much to lay. For
        # now let us bet the minimum amount possible.  For this we
        # should note that BDAQ has a minimum bet of 0.5, and BF has a
        # minimum bet of 2.0.  First the lay bet: if we are laying on
        # BDAQ, we want to lay the smallest amount possible such that
        # the matching back is for 2.0.  If we are laying on BF, again
        # we want to lay the minimum amount possible such that the back
        # is at least 0.5.
        bstake, lstake = self.get_stakes(sback.exid, self.oback,
                                         slay.exid, self.olay)

        # create both back and lay orders.         
        self.border = order.Order(sback.exid, sback.id, bstake,
                                  self.oback, 1, **{'mid': sback.mid})
        self.lorder = order.Order(slay.exid, slay.id, lstake,
                                  self.olay, 2, **{'mid': slay.mid})

    def get_stakes(self, bexid, oback, lexid, olay):
        """Return back and lay stakes."""

        # let's choose to back the minimum amount possible so we take
        # all our winnings NOW (see strategy notes). This means that
        # laystake/backstake = oback/olay * (1 - commisionback) (see
        # notes):
        lbratio = (oback/olay)* (1 - _COMMISSION[bexid])        

        backstake = max(_MINBETS[bexid], _MINBETS[lexid]/lbratio)
        laystake = lbratio*backstake
        print backstake, laystake
        # watch out for rounding errors, we may want to be a bit
        # careful here.
        return round(backstake,2), round(laystake,2)

    def make_back_order(self):
        """Place the back order"""
        if self.border.exid == const.BDAQID:
            # call bdaq api method
            print "placing BDAQ back: {0} @ {1} for ${2}".format(self.sback.name,
                                                                 self.oback,
                                                                 self.border.stake)
            # this just puts it in the list to be placed.  The
            # actually placement is done by the main program.
            self.toplace[const.BDAQID] = [self.border]
        else:
            # call BF api method
            print "placing BF back: {0} @ {1} for ${2}".format(self.sback.name,
                                                               self.oback,
                                                               self.border.stake)
            # this just puts it in the list to be placed.            
            self.toplace[const.BFID] = [self.border]


    def make_lay_order(self):
        """Place the lay order"""
        if self.lorder.exid == const.BDAQID:
            # call bdaq api method
            # dummy for now
            print "placing BDAQ lay: {0} @ {1} for ${2}".format(self.slay.name,
                                                                self.olay,
                                                                self.lorder.stake)
            self.toplace[const.BDAQID] = [self.lorder]
        else:
            print "placing BF lay: {0} @ {1} for ${2}".format(self.slay.name,
                                                              self.olay,
                                                              self.lorder.stake)
            self.toplace[const.BFID] = [self.lorder]
            # call BF api method
            pass

    def back_order_matched(self):
        """Return true if the back order has been matched, else false"""
        if self.border.status == order.MATCHED:
            return True
        return False

    def lay_order_matched(self):
        """Return true if the lay order has been matched, else false"""
        if self.lorder.status == order.MATCHED:
            return True
        return False
    
    def _backlay(self, bprice, lprice):
        """Return True if back-lay strategy profitable, else False"""
        if bprice > lprice / ((1.0 - _COMMISSION[const.BDAQID])*\
                              (1.0 - _COMMISSION[const.BFID])):
            # only interested in opportunities for which lay odds are
            # less than 20 for now.
            if lprice < 20:
                return True
        return False

    def update(self):
        # important: clear the list of orders to be placed so that we don't
        # place them again.
        self.toplace = {const.BDAQID: [], const.BFID: []}        
        
        # update prices of selections from DB
        self.sel1 = self.dbman.ReturnSelections(('SELECT * FROM selections '
                                                 'where exchange_id = ? and '
                                                 'market_id = ? and '
                                                 'selection_id = ?'),
                                                (self.sel1.exid,
                                                 self.sel1.mid,
                                                 self.sel1.id))[0]
        self.sel2 = self.dbman.ReturnSelections(('SELECT * FROM selections '
                                                 'where exchange_id = ? and '
                                                 'market_id = ? and '
                                                 'selection_id = ?'),
                                                (self.sel2.exid,
                                                 self.sel2.mid,
                                                 self.sel2.id))[0]
        # update status of any orders from DB (only orders that have
        # actually been placed.
        if hasattr(self, 'border') and self.border.status != order.NOTPLACED:
            self.border = self.dbman.ReturnOrders(('SELECT * FROM orders '
                                                  'where exchange_id = ? and '
                                                  'order_id = ?'),
                                                  self.border.exid,
                                                  self.border.oref)
        if hasattr(self, 'lorder') and self.lorder.status != order.NOTPLACED:
            self.lorder = self.dbman.ReturnOrders(('SELECT * FROM orders '
                                                  'where exchange_id = ? and '
                                                  'order_id = ?'),
                                                  self.lorder.exid,
                                                  self.lorder.oref)
        
        # AI
        self.brain.update()

class MMStrategy(strategy.Strategy):
    """Market making strategy"""
    def __init__(self):
        super(CXStrategy, self).__init__()

class CXStateInstantOpp(strategy.State):
    """An instant opportunity"""
    def __init__(self, cxstrat):
        super(CXStateInstantOpp, self).__init__('instantopp')
        self.cxstrat = cxstrat

    def entry_actions(self):
        # place both bets on the to be placed list
        self.cxstrat.toplace[self.border.exid] = border
        self.cxstrat.toplace[self.lorder.exid] = lorder        
        
        #self.cxstrat.make_back_order()
        #self.cxstrat.make_lay_order()

        # change state again
        self.cxstrat.brain.set_state('bothplaced')

class CXStateLayPlaced(strategy.State):
    """Lay bet placed (not matched as far as we know)"""
    def __init__(self, cxstrat):
        super(CXStateLayPlaced, self).__init__('layplaced')
        self.cxstrat = cxstrat

    def check_conditions(self):
        # need to
        # 1. check that the bet has been accepted
        # 2. if so, put on the back bet
        # 3. if not, are we still the best lay?
        # 4. if we are not still the best lay, can we move to be the best lay
        #    and make the strategy viable? (if so alter the lay bet)
        
        lmatch = self.cxstrat.lay_order_matched()

        if lmatch:
            return 'laymatched'
        # if lay bet not matched, don't change the state
        return None

    def exit_actions(self):
        """Place the back bet."""
        self.cxstrat.make_back_order()

class CXStateBothPlaced(strategy.State):
    """Both bets placed (neither matched as far as we know)"""
    def __init__(self, cxstrat):
        super(CXStateBothPlaced, self).__init__('bothplaced')
        self.cxstrat = cxstrat

    def check_conditions(self):
        # check if either order or both have been matched,
        bmatch = self.cxstrat.back_order_matched()
        lmatch = self.cxstrat.lay_order_matched()

        if bmatch:
            if lmatch:
                return 'bothmatched'
            else:
                return 'backmatched'
        elif lmatch:
            return 'laymatched'
        # if neither bet matched, don't change the state
        return None

class CXStateLayMatched(strategy.State):
    """Lay bet matched, back bet placed"""
    def __init__(self, cxstrat):
        super(CXStateLayMatched, self).__init__('laymatched')
        self.cxstrat = cxstrat

    def check_conditions(self):
        # check if the back bet has been matched
        bmatch = self.cxstrat.back_order_matched()

        if bmatch:
            # the trade has been completed
            return 'bothmatched'
    
class CXStateBackMatched(strategy.State):
    """Back bet matched"""
    def __init__(self, cxstrat):
        super(CXStateBackMatched, self).__init__('backmatched')
        self.cxstrat = cxstrat

class CXStateBothMatched(strategy.State):
    """Both bets matched"""
    def __init__(self, cxstrat):
        super(CXStateBothMatched, self).__init__('bothmatched')
        self.cxstrat = cxstrat

    def check_conditions(self):
        # the trade has been completed, go back to 'noopp' state
        return 'noopp'

class CXStateOpp(strategy.State):
    """An opportunity"""
    def __init__(self, cxstrat):
        super(CXStateOpp, self).__init__('opp')
        self.cxstrat = cxstrat

    def entry_actions(self):
        # place lay bet
        self.cxstrat.make_lay_order()

        # change state again
        self.cxstrat.brain.set_state('layplaced')

    def do_actions(self):
        pass
        
class CXStateNoOpp(strategy.State):
    """No betting opportunity"""
    def __init__(self, cxstrat):
        super(CXStateNoOpp, self).__init__('noopp')
        self.cxstrat = cxstrat

    def do_actions(self):
        # refresh prices from database
        pass

    def check_conditions(self):
        # check if there is an instant opportunity
        if self.cxstrat.check_instant_opportunity():
            return 'instantopp'
        elif self.cxstrat.check_opportunity():
            return 'opp'
        # if no opportunities, don't change state
        return None
