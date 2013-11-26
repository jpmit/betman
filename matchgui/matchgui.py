import wx
import os
import wx.lib.scrolledpanel as scrolledpanel
from betman.matchmarkets.matchconst import EVENTMAP
import matchguifunctions

class MyApp(wx.App):
    def OnInit(self):
        self.frame = MyFrame(None, size=(800, 600), title="Match GUI")
        self.SetTopWindow(self.frame)
        self.frame.Show()
        
        return True

class MyFrame(wx.Frame):
    def __init__(self, parent, id=wx.ID_ANY, title="",
                 pos=wx.DefaultPosition, size=wx.DefaultSize,
                 style=wx.DEFAULT_FRAME_STYLE,
                 name="MyFrame"):
        super(MyFrame, self).__init__(parent, id, title,
                                      pos, size, style, name)

        # Two panel layout
        self.rpanel = MainPanel(self)#, pos=(200,200), size=(200,200))
        self.epanel = EventPanel(self)

        # Layout
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(self.epanel, 1, wx.EXPAND)
        sizer.Add(self.rpanel, 3, wx.EXPAND)
        self.SetSizer(sizer)
        #self.SetInitialSize()
        ## #self.panel.SetBackgroundColour(wx.BLACK)

        # Logo
        path = os.path.abspath("./logo.png")
        icon = wx.Icon(path, wx.BITMAP_TYPE_PNG)
        self.SetIcon(icon)

        # StatusBar
        self.CreateStatusBar()

class MainPanel(wx.Panel):
    def __init__(self, parent, *args, **kwargs):
        super(MainPanel, self).__init__(parent, *args, **kwargs)
        
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
        sizer.AddSpacer(20)

        self.lst = MatchListCtrl(self, ename) 
        sizer.Add(self.lst, 1, wx.EXPAND)
        self.SetSizer(sizer)
        self.Layout()
        #self.SetInitialSize()

        # Event Handlers
        self.Bind(wx.EVT_LIST_ITEM_SELECTED,
                  self.OnItemSelected)
        self.Bind(wx.EVT_LIST_ITEM_RIGHT_CLICK,
                  self.OnRightClick)
        self.Bind(wx.EVT_LIST_ITEM_ACTIVATED,
                  self.OnDClick)

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
        # Show what was selected in the frames status bar
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
        """Zoom to market prices etc."""

        selected_row = event.GetIndex()
        selected_event = self.GetTopLevelParent().epanel.\
                         GetSelectedEvent()
        # market name
        name = self.lst.GetItem(selected_row, 0).GetText()
        self.PopulateMarket(selected_event, name, selected_row)
        print 'double clicked!!!'

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
        
class EventPanel(scrolledpanel.ScrolledPanel):
    def __init__(self, parent, style=wx.TAB_TRAVERSAL|wx.BORDER_SUNKEN):
        super(EventPanel, self).__init__(parent, style=style)

        # store right hand side panel
        self.rpanel = parent.rpanel

        # Attributes
        self.enames = EVENTMAP.keys()
        self.enames.sort()
        self.sizer = wx.BoxSizer(wx.VERTICAL)

        # Setup
        for ename in self.enames:
            self.AppendEvent(ename)
        self.SetSizer(self.sizer)
        self.SetupScrolling(scroll_x=False)

        # store whether one is clicked
        self.selected_obj = None
        # selected event name
        self.ename = None

    def AppendEvent(self, ename):
        """Add another event."""
        
        ebtn = wx.Button(self, size=(200,30),
                         label = ename)
        self.sizer.Add(ebtn, 1, wx.TOP, 5)

        # add the event handler
        self.Bind(wx.EVT_BUTTON, self.OnEventClick, ebtn)

    def OnEventClick(self, event):
        if self.selected_obj:
            self.selected_obj.SetBackgroundColour(None)
            
        self.selected_obj = event.GetEventObject()
        self.selected_obj.SetBackgroundColour('yellow')
        self.ename = self.selected_obj.GetLabel()
        self.rpanel.Populate(self.ename)

    def GetSelectedEvent(self):
        return self.ename

if __name__ == "__main__":
    app = MyApp(False)
    app.MainLoop()

## class MainWindow(wx.Frame):
##     def __init__(self, parent):
##         self.app = wx.App(False)
##         wx.Frame.__init__(self, parent, size=(800,600))
##         self.draw_ui()

##     def main_loop(self):
##         self.Show()
##         self.app.MainLoop()

##     def draw_ui(self):
##         """Draw welcome screen with events listed down side."""

##         from betman.matchmarkets.matchconst import EVENTMAP
##         # BDAQ event names
##         enames = EVENTMAP.keys()
##         enames.sort()

##         # need a panel apparently(?)
##         pnl = wx.ScrolledWindow(self)
##         for (i, name) in enumerate(enames):
##             ebtn = wx.Button(pnl, label = name, pos = (20, 30*(2*i + 1)))

## frame = MainWindow(None)
## frame.main_loop()

