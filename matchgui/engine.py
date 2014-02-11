from betman.strategy import strategy
import managers

"""The main engine of the betting application.

The engine is structured so that it should function independently of
the frontend, which could be a GUI (e.g. wxPython) or instead
command-line based.

"""

class Engine(object):
    def __init__(self, config):
        """Setup configuration of the engine."""

        # create a new strategy group, which stores all currently
        # executing strategies.
        self.stratgroup = strategy.StrategyGroup()

        # we have a pricing manager to handle the prices dictionary,
        # and an order manager to handle the orders dictionary.
        self.setup_managers(config)

        # automations (automatic programs for adding and removing
        # strategies).
        self.automations = []

        # counter to store how many times we have ticked
        self.ticks = 0L

    def setup_managers(self, config):
        """Setup order manager and pricing manager."""
        
        # we pass config to the order manager since we only want to
        # make orders when not in 'practice mode'.
        self.omanager = managers.OrderManager(self.stratgroup, config)
        self.pmanager = managers.PricingManager(self.stratgroup)

    def add_automation(self, myauto):

        self.automations.append(myauto)

    def remove_automation(self, myauto):

        self.automations.remove(myauto)

    def add_strategy(self, strat):
        
        self.stratgroup.add(strat)

    def remove_strategy(self, strat):
        
        self.stratgroup.remove(strat)

    def get_strategies(self):
        """Return list of currently executing strategies."""

        return self.stratgroup.strategies

    def have_strategies(self):
        """Do we have at least one currently executing strategy?

        If so, return True, otherwise return False.

        """

        if self.stratgroup.strategies:
            return True
        return False

    def have_automations(self):
        """Do we have at least one currently executing automation?

        If so, return True, otherwise return False.

        """

        if self.automations:
            return True
        return False

    def tick(self):
        """Main loop called every tick."""

        self.ticks += 1

        # handle any 'automations' we have.  All this does is adds or
        # removes strategies.  We only do this every 60 ticks (60
        # seconds if timebase is set to be 1 second).
        if (self.ticks % 60) == 0:
            for a in self.automations:
                # note we are passing a the automation a reference to
                # the engine, which it needs in order to add/remove
                # strategies to the strategy group.
                a.update(self)

        # update the status of any outstanding (unmatched) orders by
        # polling BF and BDAQ.
        self.omanager.update_order_information()

        # feed the current order dictionary just updated to the
        # strategies.
        self.stratgroup.update_orders(self.omanager.orders)

        # get prices for any strategies in the strategy group that
        # want new prices this tick by polling BF and BDAQ.
        self.pmanager.update_prices(self.ticks)

        # update strategies which got new prices this tick.  As well
        # as feeding the strategy the new prices, we do the thinking
        # 'AI' here, changing state, generating any new orders etc.
        self.stratgroup.update_prices_if(self.pmanager.prices,
                                         managers.UPDATED)

        # make any new orders (note we only make new orders for
        # strategies that got new prices this tick, see managers.py).
        self.omanager.make_orders()

        print 'TICKS', self.ticks
