# mmstrategy.py
# James Mithen
# jamesmithen@gmail.com

"""Market making strategy."""

from betman import const, order, exchangedata
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

    # if added by an automation, this sets the ttl before we close out
    # the position.
    TTL_CLOSE = 60
    
    def __init__(self, sel=None, auto=False):
        """
        sel  - selection (either BDAQ or BF).
        auto - have we been added by an automation?
        """
        
        super(MMStrategy, self).__init__()

        self.sel = sel

        # if auto is true, then we expect to be updated by the
        # automation.  This will tell us, e.g. our time to live.
        self.auto = auto

        # The ttl (time to live in seconds) is the time before the
        # strategy is removed from the engine.  It is only relevant
        # for when the strategy is added by an 'automation', in which
        # case self.auto above will be True. Initially we set the ttl
        # to be a large (arbitrary) value.  This variable will be
        # updated by the automation. It can be used by the various
        # strategy states e.g. to close out the position if there is
        # only 60 seconds left and we have unmatched bets.  Note that
        # if the strategy is not added by an automation, it is never
        # updated.
        self.ttl = 1000000.0

        self.init_state_machine()

    def init_state_machine(self):

        # add states
        noopp_state = MMStateNoOpp(self)
        opp_state = MMStateOpp(self)
        both_placed_state = MMStateBothPlaced(self)
        back_matched_state = MMStateBackMatched(self)
        lay_matched_state = MMStateLayMatched(self)
        both_matched_state = MMStateBothMatched(self)
        finished_state = MMStateFinished(self)

        self.brain.add_state(noopp_state)
        self.brain.add_state(opp_state)
        self.brain.add_state(both_placed_state)
        self.brain.add_state(back_matched_state)
        self.brain.add_state(lay_matched_state)
        self.brain.add_state(both_matched_state)
        self.brain.add_state(finished_state)

        # initialise into noopp state
        self.brain.set_state(noopp_state.name)

    def __str__(self):
        return '{0} ({1})'.format(self.sel.name, self.sel.exid)

    def get_marketids(self):
        return {self.sel.exid: [self.sel.mid]}

    def find_order_in_dict(self, order, orders):
        """Find order in dict (to get oref)

        This assumes we didn't just make more than one bet on a
        selection on the given exchange with a single polarity.

        """

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

    def update_orders(self, ostore):
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
                border = ostore.get_order(self.border.exid, self.border.oref)
                if border is not None:
                    self.border = border
            else: # we need to figure out which order in the orders
                  # dictionary is ours! (we should only have to do
                  # this once, on the tick after which the order was
                  # placed).
                  border = self.find_order_in_dict(self.border, ostore.orders_tosearch)
                  if border:
                      print 'found order with id', border.oref, border.polarity, border.price, border.stake, border.status
                      self.border = border
                      # add the order to the list of successfully
                      # placed orders
                      self.allorefs[border.exid].append(border.oref)
                  else:
                      print 'warning: could not find border in dictionary!'

        if hasattr(self, 'lorder'):
            if hasattr(self.lorder, 'oref'):
                # we already know the order reference, just see if the
                # order has changed.
                lorder = ostore.get_order(self.lorder.exid, self.lorder.oref)
                if lorder is not None:
                    self.lorder = lorder
            else: # we need to figure out which order in the orders
                  # dictionary is ours! (we should only have to do
                  # this once, on the tick after which the order was
                  # placed).
                  lorder = self.find_order_in_dict(self.lorder, ostore.orders_tosearch)
                  if lorder:
                      print 'found order with id', lorder.oref, lorder.polarity, lorder.price, lorder.stake, lorder.status
                      self.lorder = lorder
                      # add the order to the list of successfully
                      # placed orders
                      self.allorefs[lorder.exid].append(lorder.oref)
                  else:
                      print 'warning: could not find lorder in dictionary!'

    def update_prices(self, prices):
        """
        Update pricing information for any selections involved in this strategy.

        prices - dictionary of prices from BDAQ and BF API.
        """
      
        # important: clear the list of orders to be placed , to be
        # cancelled and to be updated, so that we don't place them
        # again (this is last update before we make orders).
        self.toplace = {const.BDAQID: [], const.BFID: []}
        self.tocancel = {const.BDAQID: [], const.BFID: []}
        self.toupdate = {const.BDAQID: [], const.BFID: []}

        # update prices of selection from dictionary.  Note: even
        # though the engine only calls this function if we just got
        # new prices for this strategy, we need to check for KeyError.
        # This is in case something went wrong in fetching the prices
        # from the API (e.g. we lost the network connection), in which
        # case the prices dict will be stale (or it could,
        # theoretically, be empty).
        try:
            self.sel = prices[self.sel.exid][self.sel.mid][self.sel.id]
        except KeyError:
            # we don't want to update AI if we didn't get new prices
            return

        # AI
        self.brain.update()

    def update_ttl(self, ttl):
        """Update time to live (if added by automation only)."""

        print 'updated ttl of strategy {0} to {1}'.format(self.sel.name, ttl)

        self.ttl = ttl

    def can_make(self):
        """Return True if we 'can' make a market here"""

        # At the moment, we will say we can make a market if we can
        # make both best back and best lay and be the only person
        # there.
        if self.sel.make_best_lay() > self.sel.make_best_back() + _EPS:
            return True
        return False

    def back_bet_matched(self):
        return (order.MATCHED == self.border.status)

    def lay_bet_matched(self):
        return (order.MATCHED == self.lorder.status)

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
                                               'cancelrunning' : True,
                                               # warning: only some BF
                                               # markets allow 'IP'
                                               # persistence!  (and
                                               # only some allow SP
                                               # persistence)
                                               'persistence' : 'NONE'})

        self.lorder = order.Order(sel.exid, sel.id, lstake,
                                  olay, 2, **{'mid': sel.mid,
                                              'src': sel.src,
                                              'wsn': sel.wsn,
                                              'sname': sel.name,
                                              'cancelrunning' : True,
                                              'persistence' : 'NONE'})

    def close_position(self):
        """
        Close current position by either (i) adjusting the price of the
        back/lay bet to get it matched, if the lay/back is already
        matched or (ii) cancelling both orders if neither the back nor
        lay bet is currently matched.
        """
        
        exid = self.sel.exid
        if self.back_bet_matched():
            # adjust lay bet, make it a 'market' order so it will get
            # matched.  Note we try to lay at one worse odds
            # (i.e. higher odds) than the current best lay, to make
            # sure the bet is matched.  We don't adjust the stake so
            # we aren't 'locking in a loss'.
            lodds = exchangedata.next_longer_odds(exid, self.sel.best_lay())
            self.lorder.update(price=lodds)
            # we also need to update the selection reset count and
            # withdrawal selection number
            self.lorder.wsn = self.sel.wsn
            self.lorder.src = self.sel.src
            self.toupdate[exid] = [self.lorder]
        elif self.lay_bet_matched():
            # adjust back bet, make it a 'market' order so it will get
            # matched.  Note we try to back at one worse odds than the
            # current best back, to make sure the bet is matched.  We
            # don't adjust the stake so we aren't 'locking in a loss'.
            bodds = exchangedata.next_shorter_odds(exid, self.sel.best_back())
            self.border.update(price=bodds)
            # we also need to update the selection reset count and
            # withdrawal selection number
            self.border.wsn = self.sel.wsn
            self.border.src = self.sel.src
            self.toupdate[exid] = [self.border]
        else:
            # neither bet matched, cancel both.  First check if both
            # orders have order refs: it could be that the orders were
            # never placed successfully, hence we have nothing to
            # cancel.
            if hasattr(self.border, 'oref') and hasattr(self.lorder, 'oref'):
                self.tocancel[exid] = [self.border, self.lorder]

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

        # if we are part of an automation and have limited time to
        # live, close out position and go into 'finished' state.
        if self.mmstrat.ttl < self.mmstrat.TTL_CLOSE:
            self.mmstrat.close_position()
            return 'finished'

class MMStateBackMatched(strategy.State):
    def __init__(self, mmstrat):
        super(MMStateBackMatched, self).__init__('backmatched')
        self.mmstrat = mmstrat

    def check_conditions(self):
        if self.mmstrat.lay_bet_matched():
            return 'bothmatched'

        # if we are part of an automation and have limited time to
        # live, close out position and go into 'finished' state.
        if self.mmstrat.ttl < self.mmstrat.TTL_CLOSE:
            self.mmstrat.close_position()
            return 'finished'

class MMStateLayMatched(strategy.State):
    def __init__(self, mmstrat):
        super(MMStateLayMatched, self).__init__('laymatched')
        self.mmstrat = mmstrat

    def check_conditions(self):
        if self.mmstrat.back_bet_matched():
            return 'bothmatched'

        # if we are part of an automation and have limited time to
        # live, close out position and go into 'finished' state.
        if self.mmstrat.ttl < self.mmstrat.TTL_CLOSE:
            self.mmstrat.close_position()
            return 'finished'

class MMStateBothMatched(strategy.State):
    def __init__(self, mmstrat):
        super(MMStateBothMatched, self).__init__('bothmatched')
        self.mmstrat = mmstrat

    def entry_actions(self):
        # change state immediately back to noop state, ready to sense
        # another opportunity.
        self.mmstrat.brain.set_state('noopp')

class MMStateFinished(strategy.State):
    def __init__(self, mmstrat):
        super(MMStateFinished, self).__init__('finished')
        self.mmstrat = mmstrat

    # we never change state or do anything here, we simply wait to be
    # removed by the automation.
