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
        #t2_sz = wx.BoxSizer(wx.HORIZONTAL)
        #t2_sz.Add(wx.StaticText(self,
        #                        label='BLOB'*20))
        #sizer.Add(t1_sz)
        sizer.AddSpacer(20)
        #sizer.Add(t2_sz)

        self.lst = MatchListCtrl(self, ename) 
        sizer.Add(self.lst, 1, wx.EXPAND)
        self.SetSizer(sizer)
        self.Layout()
        #self.SetInitialSize()

        # Event Handlers
        self.Bind(wx.EVT_LIST_ITEM_SELECTED,
                  self.OnItemSelected)

    def OnItemSelected(self, event):
        selected_row = event.GetIndex()
        val = []
        for column in range(3):
            item = self.lst.GetItem(selected_row, column)
            val.append(item.GetText())
        # Show what was selected in the frames status bar
        frame = self.GetTopLevelParent()
        frame.PushStatusText(",".join(val))

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
                    '0.0',
                    '0.0')
            # add the item to the list box
            self.Append(item)

        self.SetColumnWidth(0, wx.LIST_AUTOSIZE)
        self.SetColumnWidth(1, 100)
        self.SetColumnWidth(2, 200)
        self.SetColumnWidth(3, 200)        
        
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
        ename = self.selected_obj.GetLabel()
        self.rpanel.Populate(ename)

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

