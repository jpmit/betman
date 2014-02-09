import wx
import const
import managers
import models
from betman.strategy import strategy
from mainframe import MyFrame
from config import GlobalConfig
import os
import sys

class MyApp(wx.App):
    """Main app instance."""
    
    # this needs to be MixedCase since it is called by wx
    def OnInit(self):
        """Setup app configuration and start engine."""

        # set up global configuration object from input file
        self.gconfig = self.ReadConfigFromFile()

        # setup the engine
        self.SetupManagers()
        self.SetupModels()
        self.SetupTimer()

        # start timer if config says so
        self.timeron = False
        if self.gconfig.EngineStart:
            self.StartTimer()

        # setup the actual GUI
        self.frame = MyFrame(None, size=(1000, 600),
                             title=const.NAME)
        self.SetTopWindow(self.frame)
        self.frame.Show()

        # automations (automatic programs for adding and removing
        # strategies)
        sys.path.append(os.path.join(os.path.dirname(__file__), 
                                     'automation'))
        self.automations = []

        # counter to store how many times we have ticked
        self.ticks = 0L

        return True

    def AddAutomation(self, afile):
        """Add automation object from file name."""
        
        print 'adding automation from {0}'.format(afile)

        # add to current automations: note the automation class must
        # be called 'MyAutomation'.
        aut = __import__(os.path.split(afile)[-1].split('.')[0])
        self.automations.append(aut.MyAutomation())

    def RemoveAutomation(self, automation):
        """Remove the automation from the app."""

        self.automations.remove(automation)

    def AddStrategy(self, sname, key, strat, bdaqsel=None, bfsel=None):
        """Add strategy to the main engine and the required models.
        
        sname   - strategy name e.g. 'BDAQ Make'
        key     - key for accessing the strategy, at the moment this is the
                  bdaq selection name.
        strat   - the actual strategy instance (already initialised)
        bdaqsel - betdaq selection object
        bfsel   - bf selection object

        We need to pass bdaqsel and bfsel when adding strategies via
        an automation, since then we won't already have the strat
        model created.  If we added the strategy via the GUI, this
        won't be a problem, since we created the strat model already
        (see pricepanel.py, function SetupGraphsAndStrategies).

        """
        
        # this will ensure the strategy is executed
        self.stratgroup.add(strat)

        if bdaqsel and bfsel:
            self.strat_models[key] = models.StrategyModel(bdaqsel, 
                                                          bfsel)

        # initialise the strategy model
        self.strat_models[key].InitStrategy(sname, strat)

    def RemoveStrategyByKey(self, key):
        """Remove the strategy from the engine and the required models.
        
        key   - key for accessing the strategy, at the moment this is the
                bdaq selection name.
        """

        self.stratgroup.remove(self.strat_models[key].strategy)
        self.strat_models[key].RemoveStrategy()        

    def RemoveStrategyByObject(self, strat):
        """Remove the strategy from the engine and the required models.
        
        strat  - the actual strategy object
        """

        self.stratgroup.remove(strat)

        # a bit inefficient
        for k,v in self.strat_models.items():
            if (strat == v):
                v.RemoveStrategy()

    def ReadConfigFromFile(self):
        # use pickle module to store config for now
        return GlobalConfig(const.CFGFILE)

    def GetConfig(self):
        return self.gconfig

    def SetupManagers(self):
        """
        Setup strategy group and managers to deal with getting new
        prices and new orders.
        """

        # strategygroup stores all currently executing strategies
        # (initialised as empty).
        self.stratgroup = strategy.StrategyGroup()

        # the managers are used to manage fetching pricing and making
        # orders for the strategy group.
        self.omanager = managers.OrderManager(self.stratgroup)
        self.pmanager = managers.PricingManager(self.stratgroup)

    def SetupModels(self):
        """
        Setup the models that may need to be updated every tick (this
        is a subset of all the models used in the application.
        """
        
        self.pmodel = models.PriceModel()
        self.mmodel = models.MatchMarketsModel()
        self.strat_models = {}
        self.graph_models = {}

        # store a key for each graph and strategy frame that is open
        self.graphs_open = {}
        self.strats_open = {}

    def SetupTimer(self):
        """
        Setup timer that calls the updates every tick.
        """

        self.timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.OnTick, self.timer)

    def StartTimer(self):
        """
        Start the timer that calls the updates every tick.
        """

        self.timeron = True
        self.timer.Start(const.TICK_LENGTH_MS)

    def StartTimerIfNotOn(self):
        if not self.timeron:
            self.StartTimer()

    def OnTick(self, event):
        """Main loop of the engine."""

        self.ticks += 1

        # handle any 'automations' we have.  All this does is adds or
        # removes strategies.  We only do this every 60 ticks (60
        # seconds if timebase is set to be 1 second).
        if (self.ticks % 1) == 0:
            for a in self.automations:
            # note we are passing a the automation a reference to the
            # app, which it needs in order to add/remove strategies to
            # the strategy group.
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

        # update the relevant models.  We pass new_prices so that we
        # can update only models whose prices were updated this tick.

        # pricing model
        self.pmodel.Update(self.pmanager.new_prices)

        # strategy models (keyed by BDAQ selection name).  note that
        # updating these models is distinct from updating the
        # underlying strategies (which is done by
        # self.stratgroup.update_if above).  The models are updated
        # here so that the views seen by the user are kept current.
        # Note also that the models are themselves responsible for
        # checking whether new information for them is contained in
        # new_prices.
        for k in self.strat_models:
            self.strat_models[k].Update(self.pmanager.new_prices)

        # graph models (keyed by BDAQ selection name).
        for k in self.graph_models:
            self.graph_models[k].Update(self.pmanager.new_prices)

        print 'TICKS', self.ticks

if __name__ == "__main__":
    app = MyApp(False)
    app.MainLoop()
