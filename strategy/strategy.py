# strategy.py
# James Mithen
# jamesmithen@gmail.com

"""Base classes Strategy, StrategyGroup, StateMachine"""

from betman import const, betlog

class Strategy(object):
    """Base class - a strategy should inherit from this."""
    
    def __init__(self):
        self.brain = StateMachine()

        # orders to place
        self.toplace = {const.BDAQID: [], const.BFID: []}

        # orders to update
        self.toupdate = {const.BDAQID: [], const.BFID: []}

        # orders to cancel
        self.tocancel = {const.BDAQID: [], const.BFID: []}

        # list of all orders successfully placed (nb, these may or may
        # not have been matched) by the strategy.  These should be
        # ordered by time placed (with the oldest order being the
        # first in the list).
        self.allorders = []
        
    def get_marketids(self):
        """
        Return market ids involved in strategy.  These should be
        returned as a dict with keys const.BDAQID and const.BFID.
        """

        return {const.BDAQID: [], const.BFID: []}

    def get_orders_to_place(self):
        """Return a dictionary of orders to be placed.

        Dictionary should have keys const.BDAQID and const.BFID.
        """

        return self.toplace

    def get_orders_to_cancel(self):
        """Return a dictionary of orders to cancel.

        Dictionary should have keys const.BDAQID and const.BFID.
        """

        return self.tocancel

    def get_orders_to_update(self):
        """Return a dictionary of orders to update.

        Dictionary should have keys const.BDAQID and const.BFID.
        """

        return self.toupdate

    def get_allorders(self):
        """Return list of all successfully placed orders."""

        return self.allorders

    def update_prices(self, prices):
        """
        Update prices of any selections using the prices dict passed
        as argument, then do the thinking and (maybe) generate new
        orders to create or cancel on the exchanges.
        """
        
        pass

    def update_orders(self, orders):
        """
        Update order information of any placed orders using the orders
        dict passed as argument, then do the thinking and (maybe)
        generate new orders to create or cancel on the exchanges.
        """

        pass

class StrategyGroup(object):
    """Stores a group (i.e. one or more) of strategies."""
    
    def __init__(self):
        self.strategies = []

    def __len__(self):
        return len(self.strategies)

    def __getitem__(self, index):
        return self.strategies[index]

    def add(self, strategy):
        self.strategies.append(strategy)

    def remove(self, strategy):
        try:
            self.strategies.remove(strategy)
        except ValueError:
            print 'no strategy found to remove'

    def clear(self):
        self.strategies = []

    def update_prices(self, prices):
        """Update all strategies in the group."""

        for strat in self.strategies:
            strat.update_prices(prices)

    def update_orders(self, orders):
        """Update all strategies in the group."""

        for strat in self.strategies:
            strat.update_orders(orders)

    def update_prices_if(self, prices, attr='__dict__'):
        """
        Update all strategies in group if attr of strategy is True.

        The default attribute will simply mean that all strategies are
        updated.
        """

        for strat in self.strategies:
            if getattr(strat, attr):
                strat.update_prices(prices)

    # not currently used (instead we are using get_orders_to_place_if)
    def get_orders_to_place(self):
        """
        Return dictionary with keys that are the exchange ids, and
        items that are lists of order objects that we want to place.
        """
        
        toplace = {const.BDAQID: [], const.BFID: []}
        for strat in self.strategies:
            # get order dictionary for each strat
            pldict = strat.get_orders_to_place()
            for k in pldict: # k is BDAQID or BFID
                toplace[k] = toplace[k] + pldict[k]
        
        return toplace

    def get_orders_to_place_if(self, attr='__dict__'):
        """
        Return dictionary with keys that are the exchange ids, and
        items that are lists of order objects that we want to place.

        We only consider strategies for which attr is True.
        """
        
        toplace = {const.BDAQID: [], const.BFID: []}
        for strat in self.strategies:
            if getattr(strat, attr):
                # get order dictionary for each strat
                pldict = strat.get_orders_to_place()
                for k in pldict: # k is BDAQID or BFID
                    toplace[k] = toplace[k] + pldict[k]
        
        return toplace

    def get_orders_to_cancel_if(self, attr='__dict__'):
        """
        Return dictionary with keys that are the exchange ids, and
        items that are lists of order objects that we want to cancel.

        We only consider strategies for which attr is True.
        """
        
        toplace = {const.BDAQID: [], const.BFID: []}
        for strat in self.strategies:
            if getattr(strat, attr):
                # get order dictionary for each strat
                pldict = strat.get_orders_to_cancel()
                for k in pldict: # k is BDAQID or BFID
                    toplace[k] = toplace[k] + pldict[k]
        
        return toplace

    def get_orders_to_update_if(self, attr='__dict__'):
        """
        Return dictionary with keys that are the exchange ids, and
        items that are lists of order objects that we want to update.

        We only consider strategies for which attr is True.
        """
        
        toplace = {const.BDAQID: [], const.BFID: []}
        for strat in self.strategies:
            if getattr(strat, attr):
                # get order dictionary for each strat
                pldict = strat.get_orders_to_update()
                for k in pldict: # k is BDAQID or BFID
                    toplace[k] = toplace[k] + pldict[k]
        
        return toplace

    def get_marketids(self):
        """Return market ids of all strategies."""
        
        mids = {const.BDAQID: [], const.BFID: []}
        for strat in self.strategies:
            # get mid dictionary for strat
            mdict = strat.get_marketids()
            for k in mids:
                mids[k] = mids[k] + mdict[k]
        # make sure the lists in dict mids contain each market id only
        # once.
        for k in mids:
            # quick and dirty way to make list entries unique (note
            # this does not preserve order).
            mids[k] = list(set(mids[k]))
        return mids

    def remove_marketids(self, exid, mids):
        """
        Remove any strategies from the group that depend on any of
        the market ids (on exchange exid) in list mids.
        """
        
        if (exid == const.BDAQID):
            s = 'BDAQ'
        else:
            s = 'BF'
        # note list(self.strategies) gives a copy of the list
        for strat in list(self.strategies):
            # get mid dictionary for strat
            mdict = strat.get_marketids()
            for mid in mdict.get(exid, []):
                if mid in mids:
                    betlog.betlog.debug('Removing strategy due to {0} mid: {1}'.\
                                        format(s, str(strat)))
                    # remove strategy
                    self.strategies.remove(strat)

class State(object):
    """Base class - a state should inherit from this."""
    
    def __init__(self, name):
        self.name = name

    def do_actions(self):
        pass

    def check_conditions(self):
        pass

    def entry_actions(self):
        pass

    def exit_actions(self):
        pass

class StateMachine(object):
    def __init__(self):
        self.states = {}
        self.active_state = None

        # store ordered list of visited states
        self.visited_states = []

    def add_state(self, state):
        self.states[state.name] = state

    def update(self):
        if self.active_state is None:
            return

        self.active_state.do_actions()

        new_state_name = self.active_state.check_conditions()

        if new_state_name is not None:
            self.set_state(new_state_name)

    def set_state(self, new_state_name):
        if self.active_state is not None:
            self.active_state.exit_actions()


        cname = (self.active_state.name if
                 self.active_state is not None else 'None')

        # store new state in visited_states list
        self.visited_states.append(new_state_name)

        self.active_state = self.states[new_state_name]
        self.active_state.entry_actions()

    def get_num_visited_states(self):
        return len(self.visited_states)

    def get_visited_states(self):
        return self.visited_states
