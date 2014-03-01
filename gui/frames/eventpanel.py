import wx
import wx.lib.scrolledpanel as scrolledpanel
from betman.matchmarkets.matchconst import EVENTMAP

class EventPanel(scrolledpanel.ScrolledPanel):
    """
    The left hand panel which displays buttons of the available
    events.
    """
    
    def __init__(self, parent, style=wx.TAB_TRAVERSAL|wx.BORDER_SUNKEN):
        super(EventPanel, self).__init__(parent, style=style)

        # Attributes
        self.enames = EVENTMAP.keys()
        self.enames.sort()
        self.sizer = wx.BoxSizer(wx.VERTICAL)

        # set minimum width of panel
        self.SetMinSize((220,0))

        # Setup
        for ename in self.enames:
            self.AppendEvent(ename)
        self.SetSizer(self.sizer)
        self.SetupScrolling(scroll_x=False)

        # store whether one is clicked
        self.selected_obj = None
        
        # selected event name
        self.ename = None

        self.Layout()

    def AppendEvent(self, ename):
        """Add another event."""
        
        ebtn = wx.Button(self, size=(200,30),
                         label = ename)
        self.sizer.Add(ebtn, 1, wx.TOP, 5)

        # add the event handler
        self.Bind(wx.EVT_BUTTON, self.OnEventClick, ebtn)

    def OnEventClick(self, event):
        """Called when an event button, e.g. 'Rugby Union', is clicked."""
        
        if self.selected_obj:
            self.selected_obj.SetBackgroundColour(None)
            
        self.selected_obj = event.GetEventObject()
        self.selected_obj.SetBackgroundColour('yellow')
        self.ename = self.selected_obj.GetLabel()

        parent = self.GetTopLevelParent()

        # populate the panel with the BF and BDAQ markets
        parent.GetMarketPanel().Populate(self.ename)

        # show the market panel if it isn't already shown
        parent.ShowMarketPanel()

        parent.GetMarketPanel().Layout()

    def GetSelectedEvent(self):
        return self.ename
