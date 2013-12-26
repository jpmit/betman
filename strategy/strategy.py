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
        
    def get_marketids(self):
        """
        Return market ids involved in strategy.  These should be
        returned as a dict with keys const.BDAQID and const.BFID.
        """
        
        pass

    def get_orders(self):
        """
        Return a list of orders involved with a strategy.  These
        should be returned as a dict with keys const.BDAQID and
        const.BFID.
        """

        pass

    def update(self, prices):
        """
        Update prices of any selections using the prices dict passed
        as argument, then do the thinking and generate orders to
        create or cancel on the exchanges.
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

    def clear(self):
        self.strategies = []

    def update(self, prices):
        """Update all strategies in the group."""

        for strat in self.strategies:
            strat.update(prices)

    def update_if(self, prices, attr):
        """
        Update all strategies in group if attr of strategy is True.
        """

        for strat in self.strategies:
            if getattr(strat, attr):
                strat.update(prices)

    def get_orders(self):
        """
        Order ids for all strategies in the group used for checking
        order status.  This shouldn't return order ids which we
        already know are matched.
        """
        
        oids = {const.BDAQID: [], const.BFID: []}
        for strat in self.strategies:
            # get mid dictionary for strat
            odict = strat.get_orders()
            for k in odict:
                oids[k] = oids[k] + odict[k]
        return oids

    def get_orders_to_place(self):
        """
        Return dictionary with keys that are the exchange ids, and
        items that are lists of order objects that we want to place.
        """
        
        toplace = {const.BDAQID: [], const.BFID: []}
        for strat in self.strategies:
            # get order dictionary for each strat
            pldict = strat.toplace
            for k in pldict:
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
        #betlog.betlog.debug("changing state from '{0}' to '{1}'".\
        #                    format(cname, new_state_name))
        self.active_state = self.states[new_state_name]
        self.active_state.entry_actions()
