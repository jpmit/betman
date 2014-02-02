import wx
from betman import const

"""Frames that are created by clicking things on the menu bar."""

class CurrentStrategiesFrame(wx.Frame):
    """Frame for user to view currently running strategies."""
    
    # 'column' width and height
    SIZE = (100, 50)
    # padding (in px)
    PAD = 5

    def __init__(self, parent):
        wx.Frame.__init__(self, parent, size=(500, 400), 
                          title='Currently Running Strategies')
        
        # need the app instance since it stores the stratgroup
        self.app = wx.GetApp()

        self.Draw()

    def Draw(self):
        panel = wx.Panel(self)

        main_sz = wx.BoxSizer(wx.VERTICAL)

        tit_sz = wx.BoxSizer(wx.HORIZONTAL)
        tit_sz.Add(wx.StaticText(self, label="Market ID", size=self.SIZE))
        tit_sz.AddSpacer(20)
        tit_sz.Add(wx.StaticText(self, label="Selection ID", size=self.SIZE))
        tit_sz.AddSpacer(20)
        tit_sz.Add(wx.StaticText(self, label="Selection Name", size=self.SIZE))
        tit_sz.AddSpacer(20)
        tit_sz.Add(wx.StaticText(self, label="Strategy", size=self.SIZE))
        main_sz.Add(tit_sz)

        for strat in self.app.stratgroup.strategies:
            h_sz = wx.BoxSizer(wx.HORIZONTAL)

            # hacky (since we don't use official Strategy object API)
            if hasattr(strat, 'sel'):
                # MM
                sel = strat.sel
            elif hasattr(strat, 'sel1'):
                # CX
                sel = strat.sel1
            elif hasattr(strat, 'strat1'):
                # BothMM
                sel = strat.strat1.sel
            else:
                # shouldn't get here, but just in case
                continue

            selname = sel.name
            sid = sel.id
            mid = sel.mid
            # name of the class that strat is an instance of
            stratname = strat.__class__.__name__

            # (TODO: reverse lookup of maket name, given mid.  May need
            # to modify some of the models in models.py to make this
            # work.)
            h_sz = wx.BoxSizer(wx.HORIZONTAL)
            h_sz.Add(wx.StaticText(self, label="{0}".format(mid), size=self.SIZE))
            h_sz.AddSpacer(self.PAD)
            h_sz.Add(wx.StaticText(self, label="{0}".format(sid), size=self.SIZE))
            h_sz.AddSpacer(self.PAD)
            h_sz.Add(wx.StaticText(self, label="{0}".format(selname), size=self.SIZE))
            h_sz.AddSpacer(self.PAD)
            h_sz.Add(wx.StaticText(self, label="{0}".format(stratname), size=self.SIZE))
            main_sz.Add(h_sz)

        # main sizer for frame
        panel.SetSizer(main_sz)
        self.Layout()

class SettingsFrame(wx.Frame):
    """Frame for user to configure global application settings."""
    
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

