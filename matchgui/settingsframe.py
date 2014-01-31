import wx

class SettingsFrame(wx.Frame):
    def __init__(self, parent):
        wx.Frame.__init__(self, parent, title='Settings')
        
        # get global config object stored in main app
        self.gconfig = wx.GetApp().gconfig

        panel = wx.Panel(self)

        # go through each binary option in global config, draw
        # checkboxes.  we are using absolute positioning for now (not
        # sizers).
        for i, opt in enumerate(self.gconfig.BINARIES):
            nm, txt, val = opt
            cb = wx.CheckBox(panel, label=txt, pos = (50,50*(i + 1)))
            cb.SetValue(self.gconfig.GetOptionByName(nm))
        
        panel.Bind(wx.EVT_CHECKBOX, self.OnCheckOption)

    def OnCheckOption(self, event):
        sender = event.GetEventObject()
        
        txt = sender.GetLabel()
        checked = sender.GetValue()

        # set the relevant option in global configuration object to checked value
        self.gconfig.SetOptionByTxt(txt, checked)
