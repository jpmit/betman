import wx

class MonitorFrame(wx.Frame):
    def __init__(self, key):
        wx.Frame.__init__(self, None, title=key)

        # store key, this is used so that we can track when the frame
        # is killed
        self.key = key
        self.panel = MonitorPanel(self)

class MonitorPanel(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent)

        self.txtctrl = wx.TextCtrl(self, style=wx.TE_READONLY | wx.TE_MULTILINE | wx.TE_DONTWRAP)
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.sizer.Add(self.txtctrl, 1, wx.LEFT | wx.TOP | wx.GROW)
        self.SetSizer(self.sizer)
        self.Fit()

        # write some initial message
        self.txtctrl.AppendText('Hello!\nSee updates from the strategy below')
        
                                   

