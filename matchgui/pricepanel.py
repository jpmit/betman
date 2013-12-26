import wx
import wx.lib.scrolledpanel as scrolledpanel
import matchguifunctions
import const
import graphframe
import models

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

        # store a dictionary of graphs that are currently open, keys
        # are again the BDAQ selection names, values are true/false
        self.graphs_open = {}

        # models for graphs.
        self.graph_models = {}

    def SetEventIndex(self, event, index):
        """
        Set event and index.  This method is sort of like a second
        initialization method, since setting the event index means
        knowing which market and hence the selections etc.
        """

        self.event = event
        self.index = index

        # remove any previous event from the panel if necessary
        self.Clear()

        # match markets model is needed so we can draw name of event
        # etc. in the price panel.
        self.mmodel = self.GetTopLevelParent().GetMarketPanel().mmodel
        self.name = self.mmodel.GetMarketName(self.event, self.index)
        self.bdaqmid, self.bfmid = self.mmodel.GetMids(self.event, self.index)

        # pricing model (shared with control panel).
        self.pmodel = self.GetTopLevelParent().GetControlPanel().pmodel
        self.pmodel.SetEventIndex(self.event, self.index)
        self.pmodel.SetMids(self.bdaqmid, self.bfmid)
        # get selection information from BDAQ and BF
        self.pmodel.InitSels()

        # draw the panel
        self.DrawLayout()
        
        # setup information from graphs
        self.SetupGraphs()

    def SetupGraphs(self):
        """
        This is only called once, immediately after we set the event
        and index.
        """
        
        for k in self.btndict:
            # set all graphs to closed
            self.graphs_open[k] = False
            
            # create a model for each selection
            self.graph_models[k] = models.GraphPriceModel(k)

            # each graph model is updated by the main price model
            self.pmodel.AddListener(self.graph_models[k].UpdatePrices)

    def GetEventIndex(self):
        return self.event, self.index

    def DrawLayout(self):
        # todo: simplify this
        
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        name_sz = wx.BoxSizer(wx.HORIZONTAL)

        # get market name
        name_sz.Add(wx.StaticText(self, label = self.name))
        main_sizer.Add(name_sz)
        main_sizer.AddSpacer(50)

        # get market selection prices for both BDAQ and BF
        bdaqsels, bfsels = self.pmodel.GetSels()

        # WARNING: this really should not be here; this code needs to
        # be reorganised
        # using the selections, initialise the strategy models
        self.GetTopLevelParent().GetControlPanel().mmmodel.InitStrategies(bdaqsels, bfsels)
        self.GetTopLevelParent().GetControlPanel().arbmodel.InitStrategies(bdaqsels, bfsels)

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
            selname = wx.StaticText(self, label = bdaqsel.name,
                                    size = (PricePanel.BSIZE[0]*2,
                                            PricePanel.BSIZE[1]*2),
                                    style = wx.ALIGN_CENTER)

            # button for graph
            selbtn = wx.Button(self, label = 'Graph')
            selbtn.Bind(wx.EVT_BUTTON,
                        lambda evt, name=dictkey: self.OnGraphButton(evt, name))
            
            selname.Wrap(2*PricePanel.BSIZE[0])
            name_sizer.AddStretchSpacer()
            name_sizer.Add(selname, 0, wx.CENTER)
            name_sizer.AddStretchSpacer()
            name_sizer.Add(selbtn, 0, wx.CENTER)
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

    def OnGraphButton(self, event, key):
        # we only open a new graph frame if we don't already have one
        # open for the selection.
        if not self.graphs_open[key]:
            frame = graphframe.GraphFrame(key)
            frame.Bind(wx.EVT_CLOSE, self.OnCloseGraph)
            frame.Show()
            self.graphs_open[key] = True

            # add listener so that when the appropriate graph model
            # updates its data, the graph can be redrawn.
            self.graph_models[key].AddListener(frame.panel.OnUpdatePrices)

    def OnCloseGraph(self, event):
        obj = event.GetEventObject()
        # remove listener
        key = obj.key
        print obj, key
        self.graph_models[key].RemoveListener(obj.panel.OnUpdatePrices)
        
        print "killed graph window with key", key
        self.graphs_open[key] = False

        # allow the window to actually be closed
        event.Skip()
        pass

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
