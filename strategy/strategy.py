# strategy.py
# James Mithen
# jamesmithen@gmail.com

# base classes for Strategy, StrategyGroup, StateMachine etc.

class Strategy(object):
    """Base class - a strategy should inherit from this."""
    def __init__(self):
        self.brain = StateMachine()
    pass

class StrategyGroup(object):
    """Stores a group (i.e. one or more) of strategies."""
    def __init__(self):
        self.strategies = []

    def add(self, strategy):
        self.strategies.append(strategy)

    def update(self):
        """Update all strategies in the group"""
        for strat in self.strategies:
            strat.update()
        

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

        self.active_state = self.states[new_state_name]
        self.active_state.entry_actions()

