import wx
import os
import const
import wx.lib.scrolledpanel as scrolledpanel
from eventpanel import EventPanel
from marketpanel import MarketPanel
from pricepanel import PricePanel
from controlpanel import ControlPanel

class MyApp(wx.App):
    """Main app instance."""
    
    def OnInit(self):
        self.frame = MyFrame(None, size=(1000, 600),
                             title=const.NAME)
        self.SetTopWindow(self.frame)
        self.frame.Show()
        
        return True

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
        # empty), but this can change.
        self._epanel = EventPanel(self)
        self._splitter = wx.SplitterWindow(self)
        self._mpanel = MarketPanel(self._splitter)
        self._ppanel = PricePanel(self._splitter)
        self._cpanel = ControlPanel(self._splitter, style = wx.BORDER_SUNKEN)
        #self._ppanel.Hide()
        #self._cpanel.Hide()
        self.ShowMarketPanel()

        # layout
        self.sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.sizer.Add(self._epanel, 0, wx.EXPAND | wx.ALL, 10)
        #self.sizer.Add(self._mpanel, 1, wx.EXPAND)
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

    def ShowMarketPanel(self):
        # stop the timer on the control panel if it is running!
        self._cpanel.StopTimerIfRunning()
        self._ppanel.Hide()
        self._mpanel.Show()
        self._splitter.SplitVertically(self._mpanel, self._cpanel)
        self._splitter.Unsplit()
        self._splitter.Layout()
        self.Layout()

    def ShowPricePanel(self):
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
