import wx
import const
import managers
import models
from betman.strategy import strategy
from mainframe import MyFrame
import os
import sys
import pickle

class GlobalConfig(object):
    """Global app config

    The main app loads this at startup.  Note we only read and save
    the global config file at startup and shutdown respectively.  We
    are using Python's pickle module to store the config file at the
    moment, though the wx.Config functionality may be worth another
    look at some point (or, given the simple nature of the
    configuration data, a plain text file with rows key=value may be
    better than pickling).
    """
    
    # allowed options that are True/False (drawn as checkboxes).  Each
    # tuple stores shortname, full text, default value.

    # BFLogin - option not yet implemented
    # EngineStart - start the timer (ticks) from startup
    # ManyMarkets - controls whether we kill strategies for a
    # particular market after navigating away from that market.
    # (currently set to False, and not yet implemented)

    BINARIES = [('BFLogin', 'Login to BF at startup', True),
                ('EngineStart', 'Start engine at startup', False),
                ('ManyMarkets', 'Keep trading on markets', True)]

    def __init__(self, cfg):
        # name of cfg file
        self.cfgname = cfg
        
        self.SetConfigFromFile()

    def SetConfigFromFile(self):
        """Called at startup only."""

        # dict with name as key [txt, val] as arg
        data = {}
        if os.path.isfile(self.cfgname):
            f = open(self.cfgname, 'rb')
            data = pickle.load(f)
            f.close()

        # go through each option in turn
        for opt in self.BINARIES:
            name, txt, default = opt
            if name in data:
                val = data[name][1]
            else:
                val = default
            self.SetOptionByName(name, val)

    def SaveCurrentConfigToFile(self):
        """Called at exit of application only."""
        
        data = {}
        for opt in self.BINARIES:
            name, txt, default = opt
            data[name] = [txt, self.GetOptionByName(name)]

        # write data to pickle
        f = open(self.cfgname, 'wb')
        pickle.dump(data, f, pickle.HIGHEST_PROTOCOL)
        f.close()

    def SetOptionByName(self, name, val):
        """Set option and save new configuration file."""
        
        setattr(self, name, val)

    def GetOptionByName(self, name):
        return getattr(self, name)

    def SetOptionByTxt(self, txtval, val):
        """Set option with text 'txt' to value 'val'."""

        # need to map txt string e.g. 'Login to BF at startup' to name
        # e.g. 'BFLogin'.
        for opt in self.BINARIES:
            name, txt, default = opt
            if txt == txtval:
                self.SetOptionByName(name, val)

class MyApp(wx.App):
    """Main app instance."""
    
    def OnInit(self):

        # set up global configuration object from input file
        self.gconfig = self.GetConfig()

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

        return True

    def AddAutomation(self, afile):
        """Add automation object from file name."""
        
        print 'adding automation from {0}'.format(afile)

        # add to current automations: note the automation class must
        # be called 'MyAutomation'.
        aut = __import__(os.path.split(afile)[-1].split('.')[0])
        self.automations.append(aut.MyAutomation())

    def GetConfig(self):
        # use pickle module to store config for now
        return GlobalConfig(const.CFGFILE)

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

        # handle any 'automations' we have.  All this does is adds or
        # removes strategies.
        if self.automations:
            for a in self.automations:
                print a # debug
                # note this can modify the strategy group
                a.update(self.stratgroup)

        # update the status of any outstanding (unmatched) orders by
        # polling BF and BDAQ.
        self.omanager.update_order_information()

        # feed the current order dictionary just updated to the
        # strategies.
        self.stratgroup.update_orders(self.omanager.orders)

        # get prices for any strategies in the strategy group that
        # want new prices this tick.
        self.pmanager.update_prices()

        # update strategies which got new prices this tick.
        self.stratgroup.update_prices_if(self.pmanager.prices,
                                         managers.UPDATED)

        # make any new orders and save
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

        print 'TICKS', self.pmanager.ticks

if __name__ == "__main__":
    app = MyApp(False)
    app.MainLoop()
