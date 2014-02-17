# cxstrategy.py
# James Mithen
# jamesmithen@gmail.com

"""
Cross exchange strategy.  These inherit from the base classes in
strategy.py.
"""

from betman import const, database, order, exchangedata, betlog
from betman.strategy import strategy
from betman.api.bdaq import bdaqapi

# commission on winnings taken from both exchanges.
_COMMISSION = {const.BDAQID: 0.05, const.BFID: 0.05}

# min bets on each exchange in GBP.  Note we can be clever placing
# bets on BF, we can have minimum bet of 0.01 on BF!
_MINBETS = {const.BDAQID: 0.5, const.BFID: 2.0}

class CXStrategy(strategy.Strategy):
    """
    Cross exchange strategy
    ex1sel - Selection object for exchange 1 (BetDaq)
    ex2sel - Selection object for exchange 2 (Betfair)
    """
    
    def __init__(self, ex1sel = None, ex2sel = None,
                 instantonly = True):
        """
        ex1sel      - BDAQ selection
        ex2sel      - BF   selection
        instantonly - if True, only look for 'instant' opportunities.
                      This means only 'taking' and not 'making'. 
        """
        
        # this gives us self.brain, a StateMachine, and self.toplace,
        # a dictionary of orders waiting to be placed (see
        # strategy.py).
        super(CXStrategy, self).__init__()
        self.sel1 = ex1sel
        self.sel2 = ex2sel

        # if this is true, we will only look for 'instant'
        # opportunities, when we can back and lay simultaneously.
        self.ionly = instantonly

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

    def __str__(self):
        return self.sel1.name

    def get_marketids(self):
        """Return dictionary of all market ids involved in strategy."""
        
        return {const.BDAQID: [self.sel1.mid],
                const.BFID: [self.sel2.mid]}
    
    def get_orders_to_place(self):
        """Return dictionary of orders to place."""
        
        # has keys const.BDAQID, const.BFID, and values that are lists
        # of order objects.
        return self.toplace

    #def get_orders(self):
    #    """
    #    Return dictionary of all order objects involved in
    #    strategy.  This is needed so that we can check the status of
    #    the orders (we only in fact really need this for the BF
    #    orders).
    #    """
    #    
    #    odict = {const.BDAQID: [], const.BFID: []}
    #    # note: we only care about checking the order status if we
    #    # don't know for sure whether or not it is matched. We also
    #    # only care about the order if it has been placed, in fact we
    #    # need it to have been placed in order to update its status.
    #    if hasattr(self, 'border'):
    #        if ((self.border.status != order.MATCHED) and
    #            (self.border.status != order.NOTPLACED)):
    #            odict[self.border.exid].append(self.border)
    #    if hasattr(self, 'lorder'):
    #        if ((self.lorder.status != order.MATCHED) and
    #            (self.lorder.status != order.NOTPLACED)):
    #            odict[self.lorder.exid].append(self.lorder)
    #    return odict
        
    def check_instant_opportunity(self):
        """
        Can I back on one exchange and lay on the other exchange
        profitably at prices that are currently on offer?.
        """
        
        self.opp = False

        for s1,s2 in [(self.sel1,self.sel2), (self.sel2,self.sel1)]:
            # lay selection at best current price
            olay = s1.best_lay()
            if olay == exchangedata.MINODDS:
                # no lay price is currently offered
                return False

            # back selection at best current price
            oback = s2.best_back()

            if oback == exchange.MAXODDS:
                return False

            if self._backlay(oback, olay):
                # TODO: the odds are good enough, we just need to check if
                # the volume is there.
                # bstake, lstake = 
                self.store_opportunity(s1, s2, olay, oback, True)
                return True
        return False
   
    def check_opportunity(self):
        """
        Can I offer a better back than currently available, and then
        back on the other exchange at the current price?
        """
        
        self.opp = False

        for s1,s2 in [(self.sel1,self.sel2), (self.sel2,self.sel1)]:
            
            # lay selection at one better than current price on offer
            olay = s1.make_best_back()

            # back selection at best current price
            oback = s2.best_back()

            # now, if the lay price is 1.01, this means that there is
            # nothing on this side of the order book.  Instead of
            # laying a large amount at this price (which is unlikely
            # to be taken), we will lay at a more competitive price,
            # but a price that still allows us to make a profit when
            # backing on the other exchange.
            if olay <= exchangedata.MINODDSPLUS1:
                # the 0.5 is arbitrary for now, this must be < 1 in
                # order to generate an opportunity.
                olay = 0.5*oback*((1.0 - _COMMISSION[const.BDAQID])*\
                                  (1.0 - _COMMISSION[const.BFID]))

                # get lay odds which are same or shorter than olay
                olay = exchangedata.closest_shorter_odds(s1.exid, olay)

                betlog.betlog.debug('Trying new odds {0}'.format(olay))

            if self._backlay(oback, olay):
                self.store_opportunity(s1, s2, olay, oback)
                return True
        return False

    def store_opportunity(self, slay, sback, olay, oback, inst=False):
        """Store details of betting opportunity."""
        
        self.opp = True
        self.slay = slay
        self.sback = sback
        self.olay = olay
        self.oback = oback
        self.instant = inst
        
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
                                  self.oback, 1, **{'mid': sback.mid,
                                                    'src': sback.src,
                                                    'wsn': sback.wsn,
                                                    'sname': sback.name})
        self.lorder = order.Order(slay.exid, slay.id, lstake,
                                  self.olay, 2, **{'mid': slay.mid,
                                                   'src': slay.src,
                                                   'wsn': slay.wsn,
                                                   'sname': slay.name})

    def get_stakes(self, bexid, oback, lexid, olay):
        """Return back and lay stakes."""

        # let's choose to back the minimum amount possible so we take
        # all our winnings NOW (see strategy notes). This means that
        # laystake/backstake = oback/olay * (1 - commisionback) (see
        # notes):
        lbratio = (oback/olay)* (1 - _COMMISSION[bexid])        

        backstake = max(_MINBETS[bexid], _MINBETS[lexid]/lbratio)
        laystake = lbratio*backstake
        betlog.betlog.debug('Backstake: ${0} Laystake: ${1}'\
                            .format(backstake, laystake))
        
        # watch out for rounding errors, we may want to be a bit
        # more careful here.
        return round(backstake, 2), round(laystake, 2)

    def make_back_order(self):
        """
        Place the back order.  Note: this does not actually make
        the order, it only puts the order in the 'toplace' dictionary.
        """
        
        if self.border.exid == const.BDAQID:
            # print diagnostic info
            betlog.betlog.debug("placing BDAQ back: {0} @ {1} for ${2}"\
                                .format(self.sback.name, self.oback,
                                        self.border.stake))
            # this just puts it in the list to be placed.  The
            # actually placement is done by the main program.
            self.toplace[const.BDAQID] = [self.border]
        else:
            # print diagnostic info            
            betlog.betlog.debug("placing BF back: {0} @ {1} for ${2}"\
                                .format(self.sback.name, self.oback,
                                        self.border.stake))
            # this just puts it in the list to be placed.            
            self.toplace[const.BFID] = [self.border]

    def make_lay_order(self):
        """
        Place the lay order.  Note: this does not actually make the
        order, it only puts the order in the 'toplace' dictionary.
        """
        
        if self.lorder.exid == const.BDAQID:
            betlog.betlog.debug("placing BDAQ lay: {0} @ {1} for ${2}"\
                                 .format(self.slay.name, self.olay,
                                         self.lorder.stake))
            self.toplace[const.BDAQID] = [self.lorder]
        else:
            betlog.betlog.debug("placing BF lay: {0} @ {1} for ${2}"\
                                .format(self.slay.name, self.olay,
                                        self.lorder.stake))
            self.toplace[const.BFID] = [self.lorder]
            # call BF api method
            pass

    def back_order_matched(self):
        """Return true if the back order has been matched, else false."""
        
        if self.border.status == order.MATCHED:
            return True
        return False

    def lay_order_matched(self):
        """Return true if the lay order has been matched, else false."""
        
        if self.lorder.status == order.MATCHED:
            return True
        return False
    
    def _backlay(self, bprice, lprice):
        """Return True if back-lay strategy profitable, else False."""
        
        if bprice > lprice / ((1.0 - _COMMISSION[const.BDAQID])*\
                              (1.0 - _COMMISSION[const.BFID])):
            return True
        return False

    def update_orders(self, orders):

        if hasattr(self, 'border'):
            if self.border.oref in orders:
                self.border = orders[self.border.oref]
        if hasattr(self, 'lorder'):
            if self.lorder.oref in orders:
                self.lorder = orders[self.lorder.oref]

        # AI
        self.brain.update()

        # if we added any orders to self.toplace, pass them through filter
        self.filter_bets()

    def update_prices(self, prices):
        """Called everytime we have new prices for the markets."""
        
        # important: clear the list of orders to be placed so that we
        # don't place them again.
        self.toplace = {const.BDAQID: [], const.BFID: []}        
        
        # update prices of selections from dictionary.  Note: even
        # though the engine only calls this function if we just got
        # new prices for this strategy, we need to check for KeyError.
        # This is in case something went wrong in fetching the prices
        # from the API (e.g. we lost the network connection), in which
        # case the prices dict will be stale (or it could,
        # theoretically, be empty).
        try:
            self.sel1 = prices[self.sel1.exid][self.sel1.mid][self.sel1.id]
            self.sel2 = prices[self.sel2.exid][self.sel2.mid][self.sel2.id]
        except KeyError:
            # we don't want to update AI if we didn't get new prices
            return
        
        # AI
        self.brain.update()

        # if we added any orders to self.toplace, pass them through filter
        self.filter_bets()

    def filter_bets(self):
        """
        Filter bets that we are about to place.  This allows us e.g.
        to remove any bets where the stakes are too high.
        """
        
        # if we are in 'bothplaced' state, the opportunity was instant
        # so we don't want to filter any bets.
        if self.brain.active_state.name == 'bothplaced':
            return

        # only interested in opportunities for which lay odds are
        # less than 20 for now and for which lay price is greater
        # than the min odds (i.e. order book is non-empty on this
        # side).
        # go through each exchange number in turn
        for ekey in self.toplace:
            for o in  self.toplace[ekey]:
                # we only need to alter some lay orders
                if o.polarity == order.LAY:
                    # if we are laying at 1.01, lay the minimum bet
                    if o.price <= exchangedata.MINODDSPLUS1:
                        #nstake = _MINBETS[ekey]
                        #betlog.betlog.debug(('Filter: changing stake from {0} '
                        #                     'to {1}'.format(o.stake,
                        #                                     nstake)))
                        #o.stake = nstake
                        # delete bets from dictionary
                        betlog.betlog.debug(('Filter: deleting bets since layprice '
                                             '{0}'.format(o.price)))
                        self.toplace = {}
                        return

                    if o.price > 20:
                        # delete bets from dictionary
                        betlog.betlog.debug(('Filter: deleting bets since layprice '
                                             '{0}'.format(o.price)))
                        self.toplace = {}
                        return

class CXStateInstantOpp(strategy.State):
    """An instant opportunity."""
    
    def __init__(self, cxstrat):
        super(CXStateInstantOpp, self).__init__('instantopp')
        self.cxstrat = cxstrat

    def entry_actions(self):
        # place both bets on the to be placed list
        self.cxstrat.toplace[self.cxstrat.border.exid] = [self.cxstrat.border]
        self.cxstrat.toplace[self.cxstrat.lorder.exid] = [self.cxstrat.lorder]

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
    """Both bets placed (neither matched as far as we know)."""
    
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
    """Lay bet matched, back bet placed."""
    
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
    """Back bet matched."""
    
    def __init__(self, cxstrat):
        super(CXStateBackMatched, self).__init__('backmatched')
        self.cxstrat = cxstrat

class CXStateBothMatched(strategy.State):
    """Both bets matched."""
    
    def __init__(self, cxstrat):
        super(CXStateBothMatched, self).__init__('bothmatched')
        self.cxstrat = cxstrat

    def check_conditions(self):
        # the trade has been completed, go back to 'noopp' state
        return 'noopp'

class CXStateOpp(strategy.State):
    """An opportunity."""
    
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
    """No betting opportunity."""
    
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
        
        # only check for non instant opportunities if we have that
        # flag set.
        if not self.cxstrat.ionly:
            if self.cxstrat.check_opportunity():
                return 'opp'
        # if no opportunities, don't change state
        return None
