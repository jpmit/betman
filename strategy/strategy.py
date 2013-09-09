# strategy.py
# James Mithen
# jamesmithen@gmail.com

# base classes for Strategy, StrategyGroup, StateMachine etc.

from betman import const
from betman.all import betlog

class Strategy(object):
    """Base class - a strategy should inherit from this."""
    def __init__(self):
        self.brain = StateMachine()

        # orders to place
        self.toplace = {const.BDAQID: [], const.BFID: []}
        
    def get_marketids(self):
        """Return market ids involved in strategy.  These should be
        returned as a dict with keys const.BDAQID and const.BFID"""
        pass

    def get_orders(self):
        """Return a list of orders involved with a strategy.  These
        should be returned as a dict with keys const.BDAQID and
        const.BFID"""
        pass

class StrategyGroup(object):
    """Stores a group (i.e. one or more) of strategies."""
    def __init__(self):
        self.strategies = []

    def add(self, strategy):
        self.strategies.append(strategy)

    def update(self):
        """Update all strategies in the group"""
        # update does the thinking and also updates any internal
        # strategy objects, e.g. refreshing the prices using the
        # database, the status of orders, etc.
        for strat in self.strategies:
            strat.update()

    def get_orders(self):
        """Order ids for all strategies in the group used for checking
        order status.  This shouldn't return order ids which we
        already know are matched."""
        oids = {const.BDAQID: [], const.BFID: []}
        for strat in self.strategies:
            # get mid dictionary for strat
            odict = strat.get_orders()
            for k in odict:
                oids[k] = oids[k] + odict[k]
        return oids

    def get_orders_to_place(self):
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
        betlog.betlog.debug("changing state from '{0}' to '{1}'".\
                            format(cname, new_state_name))
        self.active_state = self.states[new_state_name]
        self.active_state.entry_actions()
