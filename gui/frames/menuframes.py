import wx
from betman import const, order
from betman.core import stores

"""Frames that are created by clicking things on the menu bar."""

class CurrentAutomationsFrame(wx.Frame):
    """Frame to view currently running 'automations'."""

    PAD = 5

    def __init__(self, parent):
        wx.Frame.__init__(self, parent, size=(300, 200), 
                          title='Automations')
        
        # need the app instance since it stores the stratgroup
        self.app = wx.GetApp()

        self.Draw()

        self.Center()

    def Draw(self):

        panel = wx.Panel(self)
        main_sz = wx.BoxSizer(wx.VERTICAL)

        main_sz.AddSpacer(self.PAD)
        for aut in self.app.engine.automations:
            h_sz = wx.BoxSizer(wx.HORIZONTAL)
            # add the name and a button to remove
            h_sz.Add(wx.StaticText(self, label="{0}".format(aut.get_name())), 0, 
                     wx.ALL, 15)
            rembut = wx.Button(self, label='remove')
            h_sz.Add(rembut)
            rembut.Bind(wx.EVT_BUTTON, 
                        lambda evt, a=aut: self.OnRemoveAutomation(evt, a))

            main_sz.Add(h_sz)
            main_sz.AddSpacer(self.PAD)

        # main sizer for frame
        panel.SetSizer(main_sz)
        panel.Layout()
        self.Layout()
    
    def OnRemoveAutomation(self, event, automation):
        """Remove automation from the app.

        Note we do not remove any currently running strategies.  So
        removing the automation simply means that it won't add any
        strategies in the future.  If we want to cancel any existing
        strategies, we need to do this manually through the GUI.

        """

        self.app.RemoveAutomation(automation)
        for child in self.GetChildren():
            child.Destroy()

        self.Draw()

class CurrentOrdersFrame(wx.Frame):

    """Frame for user to view/edit current orders."""    

    PAD = 5

    def __init__(self, parent):
        wx.Frame.__init__(self, parent, size=(300, 200), 
                          title='Orders')

        self.parent = parent
        self.Draw(self.parent)

        self.Center()

    def Draw(self, parent):

        panel = wx.Panel(self)
        main_sz = wx.BoxSizer(wx.VERTICAL)
        main_sz.AddSpacer(self.PAD)

        omodel = parent.omodel
        for odict in [omodel.GetBDAQOrders(), omodel.GetBFOrders()]:
            for oref in odict:
                o = odict[oref]
                h_sz = wx.BoxSizer(wx.HORIZONTAL)
                # add the name and a button to remove
                h_sz.Add(wx.StaticText(self, label="{0}".format(oref)))
                h_sz.AddSpacer(20)
                h_sz.Add(wx.StaticText(self, label = 'BDAQ' if o.exid == const.BDAQID else 'BF'))
                h_sz.AddSpacer(20)
                h_sz.Add(wx.StaticText(self, label = 'back' if o.polarity == order.BACK else 'lay'))
                h_sz.AddSpacer(20)
                h_sz.Add(wx.StaticText(self, label = '{:.2f}'.format(o.price)))
                h_sz.AddSpacer(20)
                h_sz.Add(wx.StaticText(self, label = '{:.2f}'.format(o.matchedstake)))
                h_sz.AddSpacer(20)            
                h_sz.Add(wx.StaticText(self, label = '{:.2f}'.format(o.unmatchedstake)))
                main_sz.Add(h_sz)
                main_sz.AddSpacer(self.PAD)

        # main sizer for frame
        panel.SetSizer(main_sz)
        panel.Layout()
        self.Layout()

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

        # market store
        self.mstore = stores.MatchMarketStore.Instance()

        self.Draw()

        self.Center()

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

        for strat in self.app.engine.get_strategies():
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
            
            # If sel is BF selection, get the BDAQ market id
            if (sel.exid == const.BFID):
                # get the BDAQ mid corresponding to the BF mid
                mid = self.mstore.get_BDAQmid_from_BFmid(sel.mid)
            else:
                mid = sel.mid

            selname = sel.name
            sid = sel.id
            # name of the class that strat is an instance of
            stratname = strat.__class__.__name__

            # (TODO: reverse lookup of maket name, given mid.  May need
            # to modify some of the models in models.py to make this
            # work.)
            h_sz = wx.BoxSizer(wx.HORIZONTAL)

            # make market id a hyperlink, that will show the market in
            # the main window when clicked.
            lab="{0}".format(mid)
            midtxt = wx.HyperlinkCtrl(self, id=wx.ID_ANY, label=lab, url=lab,
                                      size=self.SIZE)
            midtxt.Bind(wx.EVT_HYPERLINK, self.OnMidClick)

            h_sz.Add(midtxt)
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
    
    def OnMidClick(self, event):
        """Show the market clicked on in the panel."""

        # note bdaqmid is a string so we need to convert to int here
        bdaqmid = int(event.GetEventObject().GetURL())

        bdaqname = self.mstore.get_name_from_BDAQmid(bdaqmid)

        # show the price panel for the market selected
        self.app.frame.GoToPricePanel(bdaqname, bdaqmid)

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

        self.Center()

    def OnCheckOption(self, event):
        sender = event.GetEventObject()
        
        txt = sender.GetLabel()
        checked = sender.GetValue()

        # set the relevant option in global configuration object to
        # checked value.
        self.gconfig.SetOptionByTxt(txt, checked)
