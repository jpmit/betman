import wx
import os
import const
import wx.lib.scrolledpanel as scrolledpanel
from eventpanel import EventPanel
from marketpanel import MarketPanel
from pricepanel import PricePanel
from controlpanel import ControlPanel
from imgpanel import SplashPanel
import managers
import betman.strategy.strategy as strategy

# each tick in the application corresponds to this time in
# milliseconds.
TICK_LENGTH_MS = 1000

class MyApp(wx.App):
    """Main app instance."""
    
    def OnInit(self):
        self.frame = MyFrame(None, size=(1000, 600),
                             title=const.NAME)
        self.SetTopWindow(self.frame)
        self.frame.Show()

        self.SetupManagers()
        self.SetupTimer()
        
        return True

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

    def SetupTimer(self):
        """
        Setup timer that
        """

        self.timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.OnTick, self.timer)
        self.timer.Start(TICK_LENGTH_MS)

    def OnTick(self, event):

        # update any outstanding orders.
        self.omanager.update_order_information()

        # get prices for any strategies in the strategy group that
        # want new prices this tick.
        self.pmanager.update_prices()

        # update strategies which got new prices this tick.
        self.stratgroup.update_if(self.pmanager.prices,
                                  managers.UPDATED)

        # make any new orders and save
        self.omanager.make_orders()

class MyFrame(wx.Frame):
    """Main window."""
    
    def __init__(self, parent, id = wx.ID_ANY, title="",
                 pos = wx.DefaultPosition, size = wx.DefaultSize,
                 style = wx.DEFAULT_FRAME_STYLE,
                 name = "MyFrame"):
        super(MyFrame, self).__init__(parent, id, title,
                                      pos, size, style, name)

        # two panel layout: the left panel is always the EventPanel.
        # The right panel starts off as a MarketPanel (which is
        # empty), but this can change to be a PricePanel.  
        self._epanel = EventPanel(self)

        self._splitter = wx.SplitterWindow(self)
        self._mpanel = MarketPanel(self._splitter)
        self._ppanel = PricePanel(self._splitter)
        self._cpanel = ControlPanel(self._splitter,
                                    style = wx.BORDER_SUNKEN)

        # splash panel is ugly place holder at the moment
        self._spanel = SplashPanel(self._splitter, 'logo.png')
        self.ShowSplashPanel()

        # layout
        self.sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.sizer.Add(self._epanel, 0, wx.EXPAND | wx.ALL, 10)
        self.sizer.Add(self._splitter, 1, wx.EXPAND)
        self.SetSizer(self.sizer)

        # logo
        path = os.path.abspath("./logo.png")
        icon = wx.Icon(path, wx.BITMAP_TYPE_PNG)
        self.SetIcon(icon)

        # menus
        menubar = wx.MenuBar()
        helpmenu = wx.Menu()
        helpmenu.Append(wx.ID_ABOUT, "About")
        menubar.Append(helpmenu, "Help")
        self.SetMenuBar(menubar)

        # StatusBar
        self.CreateStatusBar()

        # event handlers
        self.Bind(wx.EVT_MENU, self.OnAbout, id = wx.ID_ABOUT)
        self.Bind(wx.EVT_CLOSE, self.OnClose)

        self.Layout()

    def OnAbout(self, event):
        """Show the about dialog."""

        info = wx.AboutDialogInfo()
        info.SetName(const.NAME)
        info.SetVersion("0.1")
        info.SetCopyright("Copyright (C) 2013 James Mithen")
        # info.SetWebSite()
        wx.AboutBox(info)

    def OnClose(self, event):
        result = wx.MessageBox("Are you sure you want to close?",
                               style=wx.CENTER|wx.ICON_QUESTION\
                               |wx.OK|wx.CANCEL, parent=self)
        if result == wx.CANCEL:
            event.Veto()
        else:
            event.Skip()

    def ShowSplashPanel(self):
        """
        In the main window show the splash panel.  This is called at
        startup only.
        """

        self._splitter.SplitVertically(self._spanel, self._cpanel)
        self._splitter.Unsplit()
        self._splitter.Layout()
        self.Layout()

    def ShowMarketPanel(self):
        """
        In the main window show the Market Panel, which displays
        matching markets for a particular event, and hide all other
        panels.
        """

        # hide the splash panel (this will only have an effect the
        # first time this fn is called).
        self._spanel.Hide()
        
        # stop the timer on the control panel if it is running! The
        # timer updates market prices.  Note we may want to change
        # this at some point.
        self._cpanel.StopUpdatesIfRunning()
        self._ppanel.Hide()
        self._mpanel.Show()
        self._splitter.SplitVertically(self._mpanel, self._cpanel)
        
        # unsplit means we only show the left panel of the splitter
        # window.
        self._splitter.Unsplit()
        self._splitter.Layout()
        self.Layout()

    def ShowPricePanel(self):
        """
        In the main window show the Price Panel, which displays prices
        for a given Market pair, alongisde the control panel.
        """
        
        self._mpanel.Hide()
        self._ppanel.Show()
        self._splitter.SplitVertically(self._ppanel, self._cpanel)
        self._splitter.Layout()
        self.Layout()

    def GetMarketPanel(self):
        return self._mpanel

    def GetEventPanel(self):
        return self._epanel

    def GetPricePanel(self):
        return self._ppanel

    def GetControlPanel(self):
        return self._cpanel

if __name__ == "__main__":
    app = MyApp(False)
    app.MainLoop()
