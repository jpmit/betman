import wx
import wx.lib.scrolledpanel as scrolledpanel
import const
import graphframe
import monitorframe
from betman.core import managers
from betman.gui import models
from betman.strategy import strategy, cxstrategy, mmstrategy, bothmmstrategy

# available strategies, names and 'constructors'
STRATEGIES = [('Arb', cxstrategy.CXStrategy),
              ('Make BDAQ', mmstrategy.MMStrategy),
              ('Make BF', mmstrategy.MMStrategy),
              ('Make Both', bothmmstrategy.BothMMStrategy)]

class PricePanel(scrolledpanel.ScrolledPanel):
    """
    Panel that shows the market prices.
    """
    
    # constants for the layout
    BSIZE = (50, 50) # button size (that displays odds and stakes)
    VGAP = 0
    HGAP = 0
    BPAD = 0 # padding around button
    BLSPACING = (10, 10) # spacing between back and lay prices

    def __init__(self, parent, *args, **kwargs):

        super(PricePanel, self).__init__(parent, *args, **kwargs)

        # we need to store a button dictionary so that we can update
        # prices.  The keys of the dictionary are the BDAQ selection
        # names.
        self.btndict = {}

        # dictionary to keep track of buttons associated with each
        # strategy.
        self.stratbtndict = {}

        # reference to main application, which stores model information.
        self.app = wx.GetApp()

        # the pricing model controls the view (the price grid).
        self.pmodel = self.app.pmodel

    def InitMids(self, mname, bdaqmid):
        """Set market name, and bdaqmid.  

        This method is sort of like a second initialization
        method,since setting these means knowing which market and
        hence the selections etc.

        """
        
        self.name = mname

        # remove any previous event from the panel if necessary
        self.Clear()

        # configure pricing model
        self.pmodel.SetBDAQMid(bdaqmid)
        
        # get selection information from BDAQ and BF; we won't get
        # fresh prices from the API via this call unless we absolutely
        # need to.
        self.pmodel.SetSels()
        
        # setup information for graphs and strategies
        self.SetupGraphsAndStrategies()

        # draw the panel
        self.DrawLayout()

    def SetupGraphsAndStrategies(self):
        """
        Create models for graphs and strategies.  This is only called
        once, immediately after we set the event and index.
        """
        
        gmodels = self.app.graph_models
        smodels = self.app.strat_models
        bdaqsels, bfsels = self.pmodel.GetSels()
        for (bdaqsel, bfsel) in zip(bdaqsels, bfsels):
            # see if current models exist for this selection,
            # otherwise create new models.  Note this means we won't
            # wipe out the old ones, important for when we navigate
            # away from a market and then return.

            if bdaqsel.name not in gmodels:
                gmodels[bdaqsel.name] = models.\
                                        GraphPriceModel(bdaqsel, bfsel)

            if bdaqsel.name not in smodels:
                smodels[bdaqsel.name] = models.\
                                        StrategyModel(bdaqsel, bfsel)

    def SetupStratForSelection(self, selname, combobox, freqspin, gobtn):
        mod = self.app.strat_models[selname]

        if not mod.HasStrategy():
            self.SetButtonAppearance(gobtn, False)
            # no existing strategy for this selection, so no need to
            # change combobox value etc.
            return
        
        strat = mod.strategy
        
        # set spinctrl to strategy frequency
        freq = getattr(strat, managers.UTICK)
        freqspin.SetValue(freq)

        # set gobtn to pressed state
        gobtn.SetValue(True)
        self.SetButtonAppearance(gobtn, True)

        # set combobox to show correct strategy name
        sname = mod.GetStringSelection()
        combobox.SetStringSelection(sname)

    def DrawLayout(self):
        # todo: simplify this
        
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        name_sz = wx.BoxSizer(wx.HORIZONTAL)

        bdaqmid, bfmid = self.pmodel.GetMids()

        # write market name at top, along with mids
        mtext = '{0}\nMIDS: BDAQ {1} BF {2}'.format(self.name, 
                                                    bdaqmid,
                                                    bfmid)
        name_sz.Add(wx.StaticText(self, label=mtext))
        main_sizer.Add(name_sz)
        main_sizer.AddSpacer(50)

        # get market selection prices for both BDAQ and BF
        bdaqsels, bfsels = self.pmodel.GetSels()

        # content_sizer holds prices on left, crossing panel on right
        content_sizer = wx.BoxSizer(wx.HORIZONTAL)
        
        # go through each selection in turn and add info to the grid
        # cells.
        for bdaqsel, bfsel in zip(bdaqsels, bfsels):

            dictkey = bdaqsel.name
            # add to the button dict
            self.btndict[dictkey] = []

            sel_sizer = wx.BoxSizer(wx.HORIZONTAL)
            sel_gridsz = wx.GridSizer(rows = 2, vgap = PricePanel.VGAP,
                                      hgap = PricePanel.HGAP)
            
            # As the name of the selection we display the BDAQ name NB
            # struggling to center this text! (it always appears in
            # the top left).
            name_sizer = wx.BoxSizer(wx.VERTICAL)
            
            # put selection name, [bdaqselid], [bfselid]
            nametxt = '\n'.join([bdaqsel.name, str(bdaqsel.id), str(bfsel.id)])
            selname = wx.StaticText(self, label = nametxt,
                                    size = (PricePanel.BSIZE[0]*2,
                                            PricePanel.BSIZE[1]*2),
                                    style = wx.ALIGN_CENTER)

            # button for graph
            graphbtn = wx.Button(self, label = 'Graph')
            graphbtn.Bind(wx.EVT_BUTTON,
                          lambda evt, name=dictkey: self.OnGraphButton(evt, name))
            
            selname.Wrap(2*PricePanel.BSIZE[0])
            name_sizer.AddStretchSpacer()
            name_sizer.Add(selname, 0, wx.CENTER)
            name_sizer.AddStretchSpacer()
            name_sizer.Add(graphbtn, 0, wx.CENTER)

            # add to main sizer for selection
            sel_sizer.Add(name_sizer, 0, wx.CENTER)
            
            # list of buttons
            pbuttons = []
            bdaqbprices = bdaqsel.padback[:const.NPRICES]
            bdaqbprices.reverse()
            bdaqlprices = bdaqsel.padlay[:const.NPRICES]
            
            for odds, stake in bdaqbprices:
                bt = wx.Button(self, size = PricePanel.BSIZE)
                if odds is None:
                    bt.SetBackgroundColour(const.GREY)
                else:
                    bt.SetBackgroundColour(const.LYELLOW)
                    bt.SetLabel('{0}\n{1}'.format(odds, stake))
                pbuttons.append((bt, 0, wx.ALL, PricePanel.BPAD))

            # add to btndict
            self.btndict[dictkey].append(pbuttons)

            sel_gridsz.AddMany(pbuttons)
            # add spacing between back and lay prices
            sel_gridsz.AddSpacer(PricePanel.BLSPACING)

            pbuttons = []
            for odds, stake in bdaqlprices:
                bt = wx.Button(self, size = PricePanel.BSIZE)
                if odds is None:
                    bt.SetBackgroundColour(const.GREY)
                else:
                    bt.SetBackgroundColour(const.LGREEN)
                    bt.SetLabel('{0}\n{1}'.format(odds, stake))
                pbuttons.append((bt, 0, wx.ALL, PricePanel.BPAD))

            # add to btndict
            self.btndict[dictkey].append(pbuttons)
            
            sel_gridsz.AddMany(pbuttons)

            # list of buttons
            pbuttons = []
            bfbprices = bfsel.padback[:const.NPRICES]
            bfbprices.reverse()
            bflprices = bfsel.padlay[:const.NPRICES]
            
            for odds, stake in bfbprices:
                bt = wx.Button(self, size = PricePanel.BSIZE)
                if odds is None:
                    bt.SetBackgroundColour(const.GREY)
                else:
                    bt.SetBackgroundColour(const.LBLUE)
                    bt.SetLabel('{0}\n{1}'.format(odds, stake))
                pbuttons.append((bt, 0, wx.ALL, PricePanel.BPAD))

            # add to btndict
            self.btndict[dictkey].append(pbuttons)

            sel_gridsz.AddMany(pbuttons)
            # add spacing between back and lay prices
            sel_gridsz.AddSpacer((20,20))

            pbuttons = []
            for odds, stake in bflprices:
                bt = wx.Button(self, size = PricePanel.BSIZE)
                if odds is None:
                    bt.SetBackgroundColour(const.GREY)
                else:
                    bt.SetBackgroundColour(const.LPINK)
                    bt.SetLabel('{0}\n{1}'.format(odds, stake))
                pbuttons.append((bt, 0, wx.ALL, PricePanel.BPAD))

            # add to btndict
            self.btndict[dictkey].append(pbuttons)

            sel_gridsz.AddMany(pbuttons)

            # add grid to selection sizer
            sel_sizer.Add(sel_gridsz)

            # add strategy stuff for this selection
            strat_sizer = wx.BoxSizer(wx.VERTICAL)            
            stratsel = wx.ComboBox(self, choices = [s[0] for s in STRATEGIES],
                                   style = wx.CB_READONLY)
            freqspin = wx.SpinCtrl(self, -1, min = 1, max = 100)            
            gobtn = wx.ToggleButton(self, label = 'Go!')
            monbtn = wx.Button(self, label = 'Monitor')

            # setup state of strategy stuff (e.g. whether 'Go' is
            # pressed, and whether the combobox shows something, based
            # on the strategy model).
            self.SetupStratForSelection(bdaqsel.name, stratsel, freqspin, gobtn)

            # add the strategy buttons as a tuple to the stratbtndict
            self.stratbtndict[dictkey] = (stratsel, freqspin, gobtn, monbtn)

            # bind strategy buttons to events
            freqspin.Bind(wx.EVT_SPINCTRL,
                          lambda evt, name=dictkey: self.OnUpdateStrategyFrequency(evt, name))
            gobtn.Bind(wx.EVT_TOGGLEBUTTON,
                       lambda evt, name=dictkey: self.OnStrategyStopStartButton(evt, name))
            monbtn.Bind(wx.EVT_BUTTON,
                        lambda evt, name=dictkey: self.OnMonitorButton(evt, name))

            # format layout of strategy stuff
            strat_sizer.Add(wx.StaticText(self, label = 'strategy'), 
                            0, wx.CENTER)
            # add the ComboBox
            strat_sizer.Add(stratsel, 0, wx.CENTER)
            strat_sizer.Add(freqspin, 0, wx.CENTER)
            strat_sizer.Add(gobtn, 0, wx.CENTER)
            strat_sizer.Add(monbtn, 0, wx.CENTER)

            # add strategy stuff to selection sizer
            sel_sizer.Add(strat_sizer)

            # add horiz sizer to the main sizer
            main_sizer.Add(sel_sizer)

            # space before next selection prices
            main_sizer.AddSpacer(20)            
                    
        self.SetSizer(main_sizer)
        self.SetupScrolling()
        self.Layout()

    def Clear(self):
        for child in self.GetChildren():
            child.Destroy()

    def OnUpdateStrategyFrequency(self, event, key):
        # only need to handle case where strategy is running
        smodel = self.app.strat_models[key]

        smodel.UpdateFrequency(event.GetEventObject().GetValue())

    def SetButtonAppearance(self, but, pressed):
        """Generic function for green/red start/stop button."""

        if pressed:
            but.SetBackgroundColour('red')
            but.SetLabel('Stop')
        else:
            but.SetBackgroundColour('green')
            but.SetLabel('Go!')

    def OnStrategyStopStartButton(self, event, key):
        """
        Add/remove strategy to/from main app strategy group at the
        desired frequency.

        key - set automatically by the Bind call to the BDAQ sel name
        """

        obj = event.GetEventObject()
        ispressed = obj.GetValue()
        self.SetButtonAppearance(obj, ispressed)

        if ispressed:
            # get the strategy selected in the corresponding
            # ComboBox. GetCurrentSelection returns the index.
            sindx = self.stratbtndict[key][0].\
                    GetCurrentSelection()
            print 'selected index', sindx, 'on combobox'

            if sindx == -1:
                # don't allow selection of the default (empty)
                # strategy type.
                obj.SetValue(False)
                return

            # get the update tick frequency from the corresponding
            # SpinCtrl.
            utick = self.stratbtndict[key][1].\
                    GetValue()
            
            print 'starting strategy', STRATEGIES[sindx][0], 'for', key
            print 'update frequency', utick

            # initialise the strategy object with the pair of
            # selections.
            sname = STRATEGIES[sindx][0]

            bdaqsel, bfsel = self.pmodel.GetSelsByBDAQName(key)

            # slightly hacky
            if 'BDAQ' in sname:
                # market make BDAQ only
                newstrat = STRATEGIES[sindx][1](bdaqsel)
            elif 'BF' in sname:
                # market make BF only
                newstrat = STRATEGIES[sindx][1](bfsel)
            elif 'Both' in sname:
                # market make BDAQ and BF
                newstrat = STRATEGIES[sindx][1](bdaqsel, bfsel)
            else:
                # cross exchange strategy
                newstrat = STRATEGIES[sindx][1](bdaqsel, bfsel)

            # set the update frequency of the strategy
            setattr(newstrat, managers.UTICK, utick)
            
            # add the strategy object to the main app strategy group
            print 'adding strategy', key
            self.app.AddStrategy(sname, key, newstrat)
        else:
            print 'removing strategy', key
            self.app.RemoveStrategyByKey(key)

    def OnMonitorButton(self, event, key):
        """
        Open a new monitor frame if we don't already have one open
        for the selection.
        """
        
        if key not in self.app.strats_open:
            
            frame = monitorframe.MonitorFrame(key)
            frame.Bind(wx.EVT_CLOSE, self.OnCloseMonitor)
            frame.Show()

            # store a reference to the frame in the dictionary
            self.app.strats_open[key] = frame

            # add listener
            self.app.strat_models[key].AddListener(frame.OnUpdateStrat)

            # update the view immediately so that we don't have to
            # wait till next time the strategy gets new prices before
            # we show something in the monitor frame.
            self.app.strat_models[key].UpdateViews()

        else:
            # bring to foreground
            self.app.strats_open[key].Raise()

    def OnGraphButton(self, event, key):
        """
        Open a new graph frame if we don't already have one open
        for the selection.
        """
        
        if key not in self.app.graphs_open:

            frame = graphframe.GraphFrame(key)
            frame.Bind(wx.EVT_CLOSE, self.OnCloseGraph)
            frame.Show()

            # store a reference to the frame in the dictionary
            self.app.graphs_open[key] = frame

            # add listener so that when the appropriate graph model
            # updates its data, the graph can be redrawn.
            self.app.graph_models[key].AddListener(frame.panel.OnUpdatePrices)

        else:
            # bring to foreground
            self.app.graphs_open[key].Raise()

    def OnCloseGraph(self, event):
        obj = event.GetEventObject()
        # get key from the GraphFrame
        key = obj.key
        print obj, key
        # remove listener        
        self.app.graph_models[key].RemoveListener(obj.panel.OnUpdatePrices)

        # delete key from graphs_open dict
        print "killed graph window with key", key
        del self.app.graphs_open[key]

        # allow the window to actually be closed
        event.Skip()

    def OnCloseMonitor(self, event):
        obj = event.GetEventObject()
        # get key from the MonitorFrame
        key = obj.key
        print obj, key
        # remove listener        
        self.app.strat_models[key].RemoveListener(obj.OnUpdateStrat)        
        
        # delete key from graphs_open dict
        print "killed monitor window with key", key
        del self.app.strats_open[key]

        # allow the window to actually be closed
        event.Skip()

    def UpdateBtnsForSelection(self, bdaqsel, bdaqbprices,
                               bdaqlprices, bfbprices,
                               bflprices):

        for (i, prices) in enumerate([bdaqbprices, bdaqlprices,
                                      bfbprices, bflprices]):
            for (j, btn) in enumerate(self.btndict[bdaqsel.name][i]):
                odds, stake = prices[j][0], prices[j][1]
                btn[0].SetLabel('{0}\n{1}'.format(odds, stake))

    def OnUpdatePrices(self, pmodel):
        """
        Draw the updated prices.  Note that this 'view' function is
        called by the listener function of the model.
        """
        
        # draw the prices onto the labels...
        print 'updating price panel!'

        bdaqsels, bfsels = pmodel.GetSels()
        for bdaqsel, bfsel in zip(bdaqsels, bfsels):
            # bdaq prices
            bdaqbprices = bdaqsel.padback[:const.NPRICES]
            bdaqbprices.reverse()
            bdaqlprices = bdaqsel.padlay[:const.NPRICES]
            # bfprices
            bfbprices = bfsel.padback[:const.NPRICES]
            bfbprices.reverse()
            bflprices = bfsel.padlay[:const.NPRICES]

            self.UpdateBtnsForSelection(bdaqsel, bdaqbprices,
                                        bdaqlprices, bfbprices,
                                        bflprices)
