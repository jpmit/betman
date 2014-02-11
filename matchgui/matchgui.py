import wx
import const
import managers
import models
from mainframe import MyFrame
from config import GlobalConfig
import os
import sys
import engine

class MyApp(wx.App):
    """Main app instance."""
    
    # this needs to be MixedCase since it is a wx method.
    def OnInit(self):
        """Setup app configuration and start engine."""

        # set up global configuration object from input file
        self.gconfig = self.ReadConfigFromFile()

        # setup the engine
        self.engine = engine.Engine(self.gconfig)

        # models for MVC style 
        self.SetupModels()

        # timer for calling the engine tick
        self.SetupTimer()

        # setup the actual GUI
        self.frame = MyFrame(None, size=(1000, 600),
                             title=const.NAME)
        self.SetTopWindow(self.frame)
        self.frame.Show()

        # add path to automations (automatic programs for adding and
        # removing strategies) so that these can be imported.
        sys.path.append(os.path.join(os.path.dirname(__file__), 
                                     'automation'))

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
        self.engine.add_strategy(strat)

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

        self.engine.remove_strategy(self.strat_models[key].strategy)
        self.strat_models[key].RemoveStrategy()        

    def RemoveStrategyByObject(self, strat):
        """Remove the strategy from the engine and the required models.
        
        strat  - the actual strategy object
        """

        self.engine.remove_strategy(strat)

        # a bit inefficient
        for k,v in self.strat_models.items():
            if (strat == v):
                v.RemoveStrategy()

    def ReadConfigFromFile(self):
        # use pickle module to store config for now
        return GlobalConfig(const.CFGFILE)

    def GetConfig(self):
        return self.gconfig

    def SetupModels(self):
        """
        Setup the models for (MVC style) that may need to be updated every
        tick NB this is a subset of all the models used in the
        application.
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

        # start timer if config says so
        self.timeron = False
        if self.gconfig.EngineStart:
            self.StartTimer()

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
        """Call the engine main loop and update the models."""
        
        # fetch prices and order information, make new orders.
        self.engine.tick()

        # update the relevant models for MVC.

        # pricing model. Note we pass new_prices so that we can update
        # only models whose prices were updated this tick.
        self.pmodel.Update(self.engine.pmanager.new_prices)

        # strategy models (keyed by BDAQ selection name).  note that
        # updating these models is distinct from updating the
        # underlying strategies (which is done by the engine).  The
        # models are updated here so that the views seen by the user
        # are kept current.  Note also that the models are themselves
        # responsible for checking whether new information for them is
        # contained in new_prices.
        for k in self.strat_models:
            self.strat_models[k].Update(self.engine.pmanager.new_prices)

        # graph models (keyed by BDAQ selection name).
        for k in self.graph_models:
            self.graph_models[k].Update(self.engine.pmanager.new_prices)

if __name__ == "__main__":
    app = MyApp(False)
    app.MainLoop()
