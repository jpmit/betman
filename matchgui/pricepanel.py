import wx
import wx.lib.scrolledpanel as scrolledpanel
import matchguifunctions

# colours for the buttons
LBLUE   = (14, 218, 249)
LPINK   = (219, 162, 197)
GREY    = (86, 86, 86)
LGREEN  = (151, 226, 176)
LYELLOW = (235, 234, 194)

class PricePanel(scrolledpanel.ScrolledPanel):
    # constants for the layout
    BSIZE = (50, 50) # button size (that displays odds and stakes)
    VGAP = 0
    HGAP = 0
    BPAD = 0 # padding around button
    BLSPACING = (10, 10) # spacing between back and lay prices

    def __init__(self, parent):

        super(PricePanel, self).__init__(parent)

    def SetEventIndex(self, event, index):

        self.event = event
        self.index = index

        # remove any previous event from the panel if necessary
        self.Clear()

        # draw the panel
        self.DrawLayout()

    def DrawLayout(self):
        
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        name_sz = wx.BoxSizer(wx.HORIZONTAL)

        # get market name
        name = matchguifunctions.market_name(self.event, self.index)
        name_sz.Add(wx.StaticText(self, label = name))
        main_sizer.Add(name_sz)
        main_sizer.AddSpacer(50)

        # get market selection prices for both BDAQ and BF
        bdaqsels, bfsels = matchguifunctions.market_prices(self.event,
                                                           self.index)

        # content_sizer holds prices on left, crossing panel on right
        content_sizer = wx.BoxSizer(wx.HORIZONTAL)
        
        # go through each selection in turn and add info to the grid
        # cells.
        for bdaqsel, bfsel in zip(bdaqsels, bfsels):

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
            selname.Wrap(2*PricePanel.BSIZE[0])
            name_sizer.AddStretchSpacer()
            name_sizer.Add(selname, 0, wx.CENTER)
            name_sizer.AddStretchSpacer()
            sel_sizer.Add(name_sizer, 0, wx.CENTER)
            
            # list of buttons
            pbuttons = []
            bdaqbprices = bdaqsel.padback[:3]
            bdaqbprices.reverse()
            bdaqlprices = bdaqsel.padlay[:3]
            
            for odds, stake in bdaqbprices:
                bt = wx.Button(self, size = PricePanel.BSIZE)
                if odds is None:
                    bt.SetBackgroundColour(GREY)
                else:
                    bt.SetBackgroundColour(LYELLOW)
                    bt.SetLabel('{0}\n{1}'.format(odds, stake))
                pbuttons.append((bt, 0, wx.ALL, PricePanel.BPAD))

            sel_gridsz.AddMany(pbuttons)
            # add spacing between back and lay prices
            sel_gridsz.AddSpacer(PricePanel.BLSPACING)

            pbuttons = []
            for odds, stake in bdaqlprices:
                bt = wx.Button(self, size = PricePanel.BSIZE)
                if odds is None:
                    bt.SetBackgroundColour(GREY)
                else:
                    bt.SetBackgroundColour(LGREEN)
                    bt.SetLabel('{0}\n{1}'.format(odds, stake))
                pbuttons.append((bt, 0, wx.ALL, PricePanel.BPAD))
            
            sel_gridsz.AddMany(pbuttons)

            # list of buttons
            pbuttons = []
            bfbprices = bfsel.padback[:3]
            bfbprices.reverse()
            bflprices = bfsel.padlay[:3]
            
            for odds, stake in bfbprices:
                bt = wx.Button(self, size = PricePanel.BSIZE)
                if odds is None:
                    bt.SetBackgroundColour(GREY)
                else:
                    bt.SetBackgroundColour(LBLUE)
                    bt.SetLabel('{0}\n{1}'.format(odds, stake))
                pbuttons.append((bt, 0, wx.ALL, PricePanel.BPAD))

            sel_gridsz.AddMany(pbuttons)
            # add spacing between back and lay prices
            sel_gridsz.AddSpacer((20,20))

            pbuttons = []
            for odds, stake in bflprices:
                bt = wx.Button(self, size = PricePanel.BSIZE)
                if odds is None:
                    bt.SetBackgroundColour(GREY)
                else:
                    bt.SetBackgroundColour(LPINK)
                    bt.SetLabel('{0}\n{1}'.format(odds, stake))
                pbuttons.append((bt, 0, wx.ALL, PricePanel.BPAD))

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
