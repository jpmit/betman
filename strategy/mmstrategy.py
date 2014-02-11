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
    """Market making strategy for a single selection.  

    This is for a single exchange only, i.e. either BDAQ or BF.
    """
    
    def __init__(self, sel = None):
        """
        sel - selection (either BDAQ or BF).
        """
        
        super(MMStrategy, self).__init__()

        self.sel = sel

        self.init_state_machine()

    def init_state_machine(self):

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

    def find_order_in_dict(self, order, orders):

        exid = order.exid
        sid = order.sid
        pol = order.polarity
        for o in orders[exid].values():
            if ((o.exid == exid) and (o.sid == sid)
                and (o.polarity == pol)):
                return o
        # no order found
        return None

    def get_orders_to_place(self):
        return self.toplace

    def update_orders(self, orders):
        """
        Update order information for any outstanding orders for this strategy.

        orders - dictionary of orders from BDAQ and BF API.
        """
        
        # TODO - fix how strategies update the order status in the
        # application to make all this cleaner.

        if hasattr(self, 'border'):
            if hasattr(self.border, 'oref'):
                # we already know the order reference, just see if the
                # order has changed.
                if self.border.oref in orders[self.border.exid]:
                    self.border = orders[self.border.exid][self.border.oref]
            else: # we need to figure out which order in the orders
                  # dictionary is ours! (we should only have to do
                  # this once, on the tick after which the order was
                  # placed).
                  border = self.find_order_in_dict(self.border, orders)
                  if border:
                      print 'found order with id', border.oref
                      self.border = border
                      # add the order to the list of successfully
                      # placed orders
                      self.allorders.append(border)
                  else:
                      print 'warning: could not find border in dictionary!'

        if hasattr(self, 'lorder'):
            if hasattr(self.lorder, 'oref'):
                # we already know the order reference, just see if the
                # order has changed.
                if self.lorder.oref in orders[self.lorder.exid]:
                    self.lorder = orders[self.lorder.exid][self.lorder.oref]
            else: # we need to figure out which order in the orders
                  # dictionary is ours! (we should only have to do
                  # this once, on the tick after which the order was
                  # placed).
                  lorder = self.find_order_in_dict(self.lorder, orders)
                  if lorder:
                      print 'found order with id', lorder.oref
                      self.lorder = lorder
                      # add the order to the list of successfully
                      # placed orders
                      self.allorders.append(lorder)
                  else:
                      print 'warning: could not find lorder in dictionary!'

    def update_prices(self, prices):
        """
        Update pricing information for any selections involved in this strategy.

        prices - dictionary of prices from BDAQ and BF API.
        """
      
        # important: clear the list of orders to be placed so that we
        # don't place them again (this is last update before we make orders).
        self.toplace = {const.BDAQID: [], const.BFID: []}

        # update selection price
        self.sel = prices[self.sel.exid][self.sel.mid][self.sel.id]

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

    def back_bet_matched(self):
        return self.border.status == order.MATCHED

    def lay_bet_matched(self):
        return self.lorder.status == order.MATCHED

    def create_orders(self):
        """Create both back and lay orders."""

        # minimum stake at the moment
        exid = self.sel.exid

        # back and lay odds
        oback = self.sel.make_best_lay()
        olay = self.sel.make_best_back()

        if exid == const.BDAQID:
            # although minimum is 0.5, there are some difficulties
            # getting this to show up when calling prices from nonAPI
            # method, so lets go for 1
            bstake = 1
        else:
            # this will be 2, the minimum bet on BF
            bstake = _MINBETS[self.sel.exid]

        # we set the lay stake so that we are 'neutral' on whether the
        # selection pays out or not.  This means laying a slightly
        # larger stake than the back stake - how much larger depends
        # on the difference in the odds.  Note we are rounding (to
        # nearest penny) here, meaning we will typically win very
        # slightly more or less if the selection comes through versus
        # if it doesn't (see my notes).  This isn't the only sensible
        # staking strategy, we can stake any value between bstake and
        # this current lstake.
        lstake = round(bstake * (1.0 + oback) / (1.0 + olay), 2)

        sel = self.sel
        
        # note we put cancelrunning = False here
        self.border = order.Order(sel.exid, sel.id, bstake,
                                  oback, 1, **{'mid': sel.mid,
                                               'src': sel.src,
                                               'wsn': sel.wsn,
                                               'sname': sel.name,
                                               # note we set both
                                               # cancel running (for
                                               # BDAQ) and persistence
                                               # (for BF)
                                               'cancelrunning' : False,
                                               'persistence' : 'IP'})
        self.lorder = order.Order(sel.exid, sel.id, lstake,
                                  olay, 2, **{'mid': sel.mid,
                                              'src': sel.src,
                                              'wsn': sel.wsn,
                                              'sname': sel.name,
                                              'cancelrunning' : False,
                                              'persistence' : 'IP'})

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
        
        # if no opportunities, don't change state
        return None

class MMStateBothPlaced(strategy.State):
    def __init__(self, mmstrat):
        super(MMStateBothPlaced, self).__init__('bothplaced')
        self.mmstrat = mmstrat

    def entry_actions(self):
        pass

    def check_conditions(self):
        # check if back or lay bet or both matched, and change state
        # accordingly.

        bm = self.mmstrat.back_bet_matched() # back bet matched
        lm = self.mmstrat.lay_bet_matched()

        if bm:
            if lm:
                return 'bothmatched'
            else:
                return 'backmatched'
        if lm:
            return 'laymatched'

class MMStateBackMatched(strategy.State):
    def __init__(self, mmstrat):
        super(MMStateBackMatched, self).__init__('backmatched')
        self.mmstrat = mmstrat

    def check_conditions(self):
        if self.mmstrat.lay_bet_matched():
            return 'bothmatched'

class MMStateLayMatched(strategy.State):
    def __init__(self, mmstrat):
        super(MMStateLayMatched, self).__init__('laymatched')
        self.mmstrat = mmstrat

    def check_conditions(self):
        if self.mmstrat.back_bet_matched():
            return 'bothmatched'

class MMStateBothMatched(strategy.State):
    def __init__(self, mmstrat):
        super(MMStateBothMatched, self).__init__('bothmatched')
        self.mmstrat = mmstrat

    def entry_actions(self):
        # change state immediately back to noop state, ready to sense
        # another opportunity.
        self.mmstrat.brain.set_state('noopp')
