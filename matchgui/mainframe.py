import wx
import const
import os
import wx.lib.scrolledpanel as scrolledpanel
import menuframes
import livebetsframe
from eventpanel import EventPanel
from marketpanel import MarketPanel
from pricepanel import PricePanel
from controlpanel import ControlPanel
from imgpanel import SplashPanel
import models

class MyFrame(wx.Frame):
    """Main window.

    This holds the menus, and manages the panels that are used.
    """
    
    def __init__(self, parent, id = wx.ID_ANY, title="",
                 pos = wx.DefaultPosition, size = wx.DefaultSize,
                 style = wx.DEFAULT_FRAME_STYLE,
                 name = "MyFrame"):

        super(MyFrame, self).__init__(parent, id, title,
                                      pos, size, style, name)

        # reference to main app
        self.app = wx.GetApp()

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

        # store dict of open frames from the menu only
        self._oframes = {'settings': None,
                         'strategies': None,
                         'automations': None,
                         'orders': None,
                         'livebets': None
                         }

        self.Layout()

    def CreateMenus(self):
        menubar = wx.MenuBar()

        # file menu
        filemenu = wx.Menu()
        filemenu.Append(wx.ID_FILE, "Load Automation")
        filemenu.Append(wx.ID_EXIT, "Exit")
        menubar.Append(filemenu, "File")
        
        # edit menu
        editmenu = wx.Menu()
        editmenu.Append(wx.ID_PREFERENCES, "Settings")
        menubar.Append(editmenu, "Edit")

        # view menu
        viewmenu = wx.Menu()
        currstrat = viewmenu.Append(wx.ID_ANY, "Current Strategies")
        currord = viewmenu.Append(wx.ID_ANY, "Current Orders")
        currauto = viewmenu.Append(wx.ID_ANY, "Current Automations")
        menubar.Append(viewmenu, "View")

        # help menu
        helpmenu = wx.Menu()
        helpmenu.Append(wx.ID_ABOUT, "About")
        menubar.Append(helpmenu, "Help")

        self.SetMenuBar(menubar)

        # bind events to menu clicks so that we show correct frames
        self.Bind(wx.EVT_MENU, self.OnLoadAutomation, id = wx.ID_FILE)
        self.Bind(wx.EVT_MENU, self.OnClose, id = wx.ID_EXIT)
        self.Bind(wx.EVT_MENU, self.OnCurrentStrategies, currstrat)
        self.Bind(wx.EVT_MENU, self.OnCurrentOrders, currord)
        self.Bind(wx.EVT_MENU, self.OnCurrentAutomations, currauto)
        self.Bind(wx.EVT_MENU, self.OnSettings, id = wx.ID_PREFERENCES)
        self.Bind(wx.EVT_MENU, self.OnAbout, id = wx.ID_ABOUT)

    def OnLoadAutomation(self, event):
        """Load an automation file."""

        dialog = wx.FileDialog(self, "Open automation", "automation/", "",
                               "Py files (*.py)|*.py", 
                               wx.FD_OPEN | wx.FD_FILE_MUST_EXIST)

        if dialog.ShowModal() == wx.ID_CANCEL:
            return

        # we only want to save the name of the file here, and the fact
        # that there is now an automation registered.
        afile = dialog.GetPath()

        # add the automation to the app: this will mean that the
        # automation gets called every tick.
        self.app.AddAutomation(afile)

    def OnCloseFrame(self, event, nm):
        """Called when we close a frame opened by a menu option."""

        print "closing frame", nm

        self._oframes[nm] = None
        print 'sucessfully set oframe to None'
        event.Skip()

    def OnSettings(self, event):
        """Show the settings frame."""

        nm = 'settings'

        frame = self._oframes[nm]
        if frame is None:
            frame = menuframes.SettingsFrame(self)
            self._oframes['settings'] = frame
            frame.Bind(wx.EVT_CLOSE, 
                       lambda e,n=nm: self.OnCloseFrame(e, n))
            frame.Show()
        else:
            frame.Raise()

    def OnAbout(self, event):
        """Show the about dialog."""
        
        # note that the about box is not modal on Linux, which is
        # apparently a bug in wxPython.  This means we can open
        # multiple about boxes.  On Windows and OS/X this is
        # apparently not a problem.  To solve the Linux problem, it
        # seems it is necessary to create a custom about box.
        info = wx.AboutDialogInfo()
        info.SetName(const.NAME)
        info.SetVersion("0.1")
        info.SetCopyright("Copyright (C) 2013-2014 James Mithen")
        # info.SetWebSite()
        wx.AboutBox(info)

    def OnCurrentStrategies(self, event):
        """Show frame with currently running strategies."""

        nm = 'strategies'

        frame = self._oframes[nm]
        if frame is None:
            if self.app.engine.have_strategies():
                if not self._oframes['strategies']:
                    frame = menuframes.CurrentStrategiesFrame(self)
                    frame.Show()
                    self._oframes[nm] = frame
                    frame.Bind(wx.EVT_CLOSE, 
                               lambda e,n=nm: self.OnCloseFrame(e, n))
            else:
                wx.MessageBox("No strategies currently running.", 
                              style=wx.CENTER|wx.OK, parent = self)
        else:
            frame.Raise()

    def OnCurrentOrders(self, event):
        """Show frame with orders made so far and their status."""

        nm = 'livebets'

        frame = self._oframes[nm]

        # MVC
        #self.omodel = models.OrderModel.Instance()

        if frame is None:
            if not self._oframes['livebets']:
                frame = livebetsframe.LiveBetsFrame(self)
                frame.Show()
                self._oframes[nm] = frame
                frame.Bind(wx.EVT_CLOSE, 
                           lambda e,n=nm: self.OnCloseFrame(e, n))
            else:
                wx.MessageBox("No orders made yet.", 
                              style=wx.CENTER|wx.OK, parent = self)
        else:
            frame.Raise()

    def OnCurrentAutomations(self, event):
        """Show frame with currently running automations."""

        nm = 'automations'

        frame = self._oframes[nm]
        if frame is None:
            if self.app.engine.have_automations():
                if not self._oframes['automations']:
                    frame = menuframes.CurrentAutomationsFrame(self)
                    frame.Show()
                    self._oframes[nm] = frame
                    frame.Bind(wx.EVT_CLOSE, 
                               lambda e,n=nm: self.OnCloseFrame(e, n))
            else:
                wx.MessageBox("No automations currently running.", 
                              style=wx.CENTER|wx.OK, parent = self)
        else:
            frame.Raise()

    def OnClose(self, event):
        result = wx.MessageBox("Are you sure you want to close?",
                               style=wx.CENTER|wx.ICON_QUESTION\
                               |wx.OK|wx.CANCEL, parent=self)
        if result == wx.CANCEL:
            if event.CanVeto():
                event.Veto()
        else:
            # save configuration file which may have been changed in
            # settings.
            self.app.gconfig.SaveCurrentConfigToFile()
            # Skip() will go allow the event to propagate to the
            # default event handler, which will destroy the window.
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

    def GoToPricePanel(self, name, bdaqmid, bfmid):
        self.ShowPricePanel()
        self._ppanel.InitMids(name, bdaqmid, bfmid)

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
