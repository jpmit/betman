import wx
import const
import os
import wx.lib.scrolledpanel as scrolledpanel
from settingsframe import SettingsFrame
from eventpanel import EventPanel
from marketpanel import MarketPanel
from pricepanel import PricePanel
from controlpanel import ControlPanel
from imgpanel import SplashPanel

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
        self.CreateMenus()

        # StatusBar
        self.CreateStatusBar()

        # event handler for close
        self.Bind(wx.EVT_CLOSE, self.OnClose)

        self.Layout()

    def CreateMenus(self):
        menubar = wx.MenuBar()

        # edit menu
        editmenu = wx.Menu()
        editmenu.Append(wx.ID_PREFERENCES, "Settings")
        menubar.Append(editmenu, "Edit")

        # help menu
        helpmenu = wx.Menu()
        helpmenu.Append(wx.ID_ABOUT, "About")
        menubar.Append(helpmenu, "Help")

        self.SetMenuBar(menubar)

        # bind events to menu clicks so that we show correct frames
        self.Bind(wx.EVT_MENU, self.OnSettings, id = wx.ID_PREFERENCES)
        self.Bind(wx.EVT_MENU, self.OnAbout, id = wx.ID_ABOUT)

    def OnSettings(self, event):
        """Show the settings frame."""

        frame = SettingsFrame(self)
        frame.Show()

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
            # save configuration file which may have been changed in
            # settings.
            wx.GetApp().gconfig.SaveCurrentConfigToFile()
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
        self._mpanel.Layout()

        # this seems to resize the panel correctly(?) NOPE
        #self._splitter.UpdateSize()

        print "size of splitter: ", self._splitter.GetSize()
        print "size of marketpanel: ", self._mpanel.GetSize()

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
