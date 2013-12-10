import wx
import matchguifunctions
from pricepanel import PricePanel
import const

class MarketPanel(wx.Panel):
    """Panel that displays a list of markets for a given event."""
    
    def __init__(self, parent, *args, **kwargs):
        super(MarketPanel, self).__init__(parent, *args, **kwargs)
        
    def Populate(self, ename):
        """
        Populate panel with matching events for the selected event
        name.
        """
        
        self.Clear()
        sizer = wx.BoxSizer(wx.VERTICAL)
        t1_sz = wx.BoxSizer(wx.HORIZONTAL)
        t1_sz.Add(wx.StaticText(self,
                                label='List of matching markets for event: {0}'\
                                .format(ename)))
        sizer.Add(t1_sz)
        sizer.AddSpacer(20)

        # __init__ of MatchListCtrl will get the events
        # show progress box
        self.dialog = wx.ProgressDialog(const.NAME,
                                        "Loading markets for {0}".format(ename),
                                        parent = self, style = wx.PD_APP_MODAL | wx.PD_SMOOTH)
        self.dialog.Pulse()
        self.timer = wx.Timer()
        self.Bind(wx.EVT_TIMER, self.Pulse, self.timer)
        self.timer.Start(100)
        self.lst = MatchListCtrl(self, ename)
        self.DestroyDialog()
        
        sizer.Add(self.lst, 1, wx.EXPAND)
        self.SetSizer(sizer)
        self.Layout()

        # Event Handlers
        self.Bind(wx.EVT_LIST_ITEM_SELECTED,
                  self.OnItemSelected)
        self.Bind(wx.EVT_LIST_ITEM_RIGHT_CLICK,
                  self.OnRightClick)
        self.Bind(wx.EVT_LIST_ITEM_ACTIVATED,
                  self.OnDClick)

    def Pulse(self, event):
        self.dialog.Pulse()

    def DestroyDialog(self):
        self.timer.Stop()
        self.dialog.Destroy()

    def PopulateMarket(self, event, name, index):
        """Give market prices etc."""
        
        self.Clear()
        sizer = wx.BoxSizer(wx.VERTICAL)
        name_sz = wx.BoxSizer(wx.HORIZONTAL)
        name_sz.Add(wx.StaticText(self, label=name))
        sizer.Add(name_sz)

        # get market selection prices for both BDAQ and BF
        bdaqsels, bfsels = matchguifunctions.market_prices(event,
                                                           index)
        print bdaqsels, bfsels

        for sel in bdaqsels:
            sz = wx.BoxSizer(wx.HORIZONTAL)
            sz.Add(wx.StaticText(self, label=sel.name))
            for p in sel.backprices:
                sz.Add(wx.StaticText(self, label=str(p) + '    '))
            sizer.AddSpacer(50)
            for p in sel.layprices:
                sz.Add(wx.StaticText(self, label=str(p) + '    '))
            sizer.Add(sz)
                    
        self.SetSizer(sizer)
        self.Layout()
        pass

    def OnItemSelected(self, event):
        """Write data on selected market to status bar."""
        
        selected_row = event.GetIndex()
        val = []
        for column in range(3):
            item = self.lst.GetItem(selected_row, column)
            val.append(item.GetText())
            
        # show what was selected in the frames status bar
        frame = self.GetTopLevelParent()
        frame.PushStatusText(",".join(val))

    def OnRightClick(self, event):
        """Create menu with options."""

        print 'trying to create a menu'
        self._menu = wx.Menu()
        self._menu.Append(wx.ID_CUT)
        self._menu.Append(wx.ID_COPY)
        self._menu.Append(wx.ID_PASTE)
        self.PopupMenu(self._menu)
        pass

    def OnDClick(self, event):
        """Change panel to the PricePanel that shows prices etc."""

        selected_row = event.GetIndex()
        selected_event = self.GetTopLevelParent().\
                         GetEventPanel().\
                         GetSelectedEvent()
        # market name
        name = self.lst.GetItem(selected_row, 0).GetText()

        # set right panel
        parent = self.GetTopLevelParent()
        parent.ShowPricePanel()

        # pass the price panel details of the event name and market
        parent.GetPricePanel().SetEventIndex(selected_event,
                                             selected_row)

    def Clear(self):
        for child in self.GetChildren():
            child.Destroy()

class MatchListCtrl(wx.ListCtrl):
    """List matching markets for event name ename."""
    
    def __init__(self, parent, ename):
        super(MatchListCtrl, self).__init__(parent,
                                            style=wx.LC_REPORT)

        # add column headings
        self.InsertColumn(0, "Market Name")
        self.InsertColumn(1, "Start Time")
        self.InsertColumn(2, "BDAQ Matched")
        self.InsertColumn(3, "BF Matched")        

        # get matching markets for the selected event
        mmarks = matchguifunctions.match_markets(ename)
        for (m1, m2) in mmarks:
            item = (m1.name.split('|')[-2],
                    m1.starttime.strftime('%d/%m/%y %H:%M'),
                    # note the BDAQ total matched did not come
                    # directly from the API here (see
                    # matchguifunctions.py).
                    m1.properties['totalmatched'],
                    m2.properties['totalmatched'])
            # add the item to the list box
            self.Append(item)

        self.SetColumnWidth(0, wx.LIST_AUTOSIZE)
        self.SetColumnWidth(1, 200)
        self.SetColumnWidth(2, 150)
        self.SetColumnWidth(3, 150)        
