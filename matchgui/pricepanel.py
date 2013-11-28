import wx
import wx.lib.scrolledpanel as scrolledpanel
import matchguifunctions

# colours for the buttons
LBLUE = (14, 218, 249)
LPINK = (219, 162, 197)
GREY = (86, 86, 86)
LGREEN = (151, 226, 176)
LYELLOW = (235, 234, 194)

class PricePanel(scrolledpanel.ScrolledPanel):

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
        name_sz.Add(wx.StaticText(self, label=name))
        main_sizer.Add(name_sz)
        main_sizer.AddSpacer(50)

        # get market selection prices for both BDAQ and BF
        bdaqsels, bfsels = matchguifunctions.market_prices(self.event,
                                                           self.index)

        sz = wx.GridSizer(rows=len(bdaqsels), vgap = 1, hgap = 1)
        for sel in bdaqsels:
            sz.Add(wx.StaticText(self, label = sel.name, style = wx.ALIGN_CENTER))

            # list of plate buttons
            pbuttons = []
            bprices = sel.padback[:3]
            bprices.reverse()
            lprices = sel.padlay[:3]
            for odds, stake in bprices:
                bt = wx.Button(self, size = (50, 50))
                #bt.SetSize((100, 30))
                if odds is None:
                    bt.SetBackgroundColour(GREY)
                else:
                    bt.SetBackgroundColour(LBLUE)
                    bt.SetLabel('{0}\n{1}'.format(odds, stake))
                pbuttons.append((bt, 0, wx.ALL, 5))
            
            for odds, stake in lprices:
                bt = wx.Button(self, size=(50, 50))
                           #           style = pbtn.PB_STYLE_SQUARE, size = (100, 30))
                #bt.SetSize((100, 30))                
                if odds is None:
                    bt.SetBackgroundColour(GREY)
                else:
                    bt.SetBackgroundColour(LPINK)
                    bt.SetLabel('{0}\n{1}'.format(odds, stake))
                pbuttons.append((bt, 0, wx.ALL, 5))
            
            sz.AddMany(pbuttons)

        # add the grid to the main sizer
        main_sizer.Add(sz)
                    
        self.SetSizer(main_sizer)
        self.SetupScrolling()
        self.Layout()

    def Clear(self):
        for child in self.GetChildren():
            child.Destroy()
