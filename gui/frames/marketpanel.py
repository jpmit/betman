import wx
import datetime
from pricepanel import PricePanel
import const
import models
from betman.core import stores
import wx.lib.mixins.listctrl as listmix

class MarketPanel(wx.Panel):
    """Panel that displays a list of markets for a given event."""
    
    def __init__(self, parent, *args, **kwargs):
        super(MarketPanel, self).__init__(parent, *args, **kwargs)

        # we don't know the event name at initialisation, we set this
        # when the user clicks an event e.g. 'Rugby Union'
        self.ename = None

        # Control stores the list of matching markets
        self.lst = MatchListCtrl(self)

        # model from market data
        self.mmodel = models.MatchMarketsModel.Instance()

        # market store has information about the markets such as name etc.
        self.mstore = stores.MatchMarketStore.Instance()
        
        # The listener will update the view
        self.mmodel.AddListener(self.lst.OnGetMatchEvents)

        self.CreateLayout()

    def CreateLayout(self):
        """
        Create the layout of the panel, and add the event handlers.
        """

        # Main sizer
        sizer = wx.BoxSizer(wx.VERTICAL)
        
        # Sizer for the title text and refresh button
        tsz = wx.BoxSizer(wx.HORIZONTAL)
        self.ttext = wx.StaticText(self)
        refbut = wx.Button(self, wx.ID_REFRESH)

        tsz.Add(self.ttext)
        tsz.Add(refbut)
        sizer.Add(tsz)
        sizer.AddSpacer(20)
        
        sizer.Add(self.lst, 1, wx.EXPAND | wx.ALL | wx.ALIGN_CENTER)
        self.SetSizer(sizer)

        # Event Handlers
        self.Bind(wx.EVT_BUTTON, self.OnRefresh, refbut)
        self.Bind(wx.EVT_LIST_ITEM_SELECTED,
                  self.OnItemSelected)
        self.Bind(wx.EVT_LIST_ITEM_RIGHT_CLICK,
                  self.OnRightClick)
        self.Bind(wx.EVT_LIST_ITEM_ACTIVATED,
                  self.OnDClick)

    def _SetEvent(self, ename):
        """
        Use the event name to set the title of the Market Panel.
        """

        self.ename = ename
        self.ttext.SetLabel('List of matching markets for event: {0}'\
                            .format(self.ename))

    def OnRefresh(self, event):
        self.mmodel.Update(self.ename, refresh = True)
        
    def Populate(self, ename):
        """
        This is called when the corresponding button on the event
        panel (on LHS) is clicked.  We populate panel with matching
        events for the selected event name.
        """
        
        # set event for the panel
        self._SetEvent(ename)

        # set event for the MatchListCtrl
        self.lst.SetEvent(ename)

        # get matching markets for this event (update the model), note
        # that the model will update the view (the ListCtrl) via its
        # listener function.
        self.mmodel.Update(ename)

        self.Layout()
        self.lst.Layout()

    def Pulse(self, event):
        self.dialog.Pulse()

    def DestroyDialog(self):
        self.timer.Stop()
        self.dialog.Destroy()

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
        """Create popup menu with options (this is for future use)."""

        self._menu = wx.Menu()
        self._menu.Append(wx.ID_CUT)
        self._menu.Append(wx.ID_COPY)
        self._menu.Append(wx.ID_PASTE)
        self.PopupMenu(self._menu)
        pass

    def OnDClick(self, event):
        """Change panel to the PricePanel that shows prices etc."""

        index_sel = event.GetIndex()

        # map the event and row to BDAQ and BF market ids and market name.
        bdaqmid = self.mmodel.GetBDAQMid(index_sel)
        name = self.mstore.get_name_from_BDAQmid(bdaqmid)

        # go to the price panel.
        self.GetTopLevelParent().GoToPricePanel(name, bdaqmid)

    def Clear(self):
        for child in self.GetChildren():
            child.Destroy()

class MatchListCtrl(wx.ListCtrl, listmix.ColumnSorterMixin):
    """List matching markets for event name ename."""
    
    def __init__(self, parent):
        super(MatchListCtrl, self).__init__(parent,
                                            style=wx.LC_REPORT)
        # event name, e.g. 'Horse Racing'
        self.ename = None

        # add column headings
        self.InsertColumn(0, "Market Name")
        self.InsertColumn(1, "Start Time (GMT)")
        self.InsertColumn(2, "BDAQ Matched")
        self.InsertColumn(3, "BF Matched")

        self.SetColumnWidth(0, wx.LIST_AUTOSIZE)
        self.SetColumnWidth(1, 200)
        self.SetColumnWidth(2, 150)
        self.SetColumnWidth(3, 150)        

    def SetEvent(self, ename):
        """Set selected event to ename, and add in the data."""

        self.ename = ename

    def OnGetMatchEvents(self, mmodel):
        """
        Listener function called by the MatchMarketsModel, to update
        the view.  We add the items, which are pairs of markets, to the ListCtrl
        """

        # we use the event name in the model to access the matching
        # markets for that event in the Market Store.
        mstore = stores.MatchMarketStore.Instance()
        mmarks = mstore.get_matches(mmodel.GetEventName())

        # Clear any existing items on the ListCtrl
        self.DeleteAllItems()

        i = 0
        markdata = {}
        for (m1, m2) in mmarks:
            item = (m1.name.split('|')[-2],
                    m1.starttime.strftime('%d/%m/%y %H:%M'),
                    m1.totalmatched,
                    m2.totalmatched)
            # add the item to the list box
            self.Append(item)
            # for sorting
            markdata[i] = item
            self.SetItemData(i, i)
            i += 1

        # stuff for sorting
        self.itemDataMap = markdata
        listmix.ColumnSorterMixin.__init__(self, 4)
        self.Bind(wx.EVT_LIST_COL_CLICK, self.OnColClick, self)

        # set column width of event name to be sufficiently large
        self.SetColumnWidth(0, wx.LIST_AUTOSIZE)

    # Used by the ColumnSorterMixin, see wx/lib/mixins/listctrl.py
    def GetListCtrl(self):
        return self

    def OnColClick(self, event):
        event.Skip()
