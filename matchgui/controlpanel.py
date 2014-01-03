import wx
import models
import const
from betman.strategy import updatestrategy
import managers

class ControlPanel(wx.Panel):
    """Panel for setting market refresh rate, etc."""

    def __init__(self, parent, *args, **kwargs):
        super(ControlPanel, self).__init__(parent, *args, **kwargs)

        # draw buttons etc.
        self.CreateLayout()

        # timer and associated events
#        self.timer = wx.Timer(self)
#        self.Bind(wx.EVT_TIMER, self.OnTimerEvent, self.timer)
        self.Bind(wx.EVT_SPINCTRL, self.OnUpdateSpinCtrl)

        # reference to the price panel, which contains the prices and
        # stakes for the currently selected market.
        ppanel = self.GetTopLevelParent().GetPricePanel()

        # models for MVC: we have (i) a pricing model, which, when
        # updated will get the latest prices and stakes for BF and
        # BDAQ, (ii) a model for the market marking strategy, which
        # will be updated by the pricing model and (iii) a model for
        # the arbitrage strategy, again updated by the pricing model.
        self.pmodel = wx.GetApp().pmodel
        self.mmmodel = models.MarketMakingModel()
        self.arbmodel = models.ArbitrageModel()

        # when the model is updated, we draw the prices and stakes
        # onto the main panel.
        self.pmodel.AddListener(ppanel.OnUpdatePrices)

        # update strategy
        self.ustrat = None
        
    def CreateLayout(self):
        sizer = wx.BoxSizer(wx.VERTICAL)
        h_sizer = wx.BoxSizer(wx.HORIZONTAL)

        self.freqspin = wx.SpinCtrl(self, -1, min = 1, max = 100)

        # button for starting / stopping refreshing prices
        self.startbut = wx.ToggleButton(self)
        self.SetStartButtonLabelColor(False)

        # button for starting market making strategy
        self.mmbutton = wx.ToggleButton(self, label = 'Make Market')
        self.mmbutton.Disable()

        # button for starting arbitrage strategy
        self.arbbutton = wx.ToggleButton(self, label = 'Arbitrage Market')
        self.arbbutton.Disable()

        # event binding for the buttons
        self.Bind(wx.EVT_TOGGLEBUTTON, self.OnStartButtonClick,
                  self.startbut)
        self.Bind(wx.EVT_TOGGLEBUTTON, self.OnMarketMakingButtonClick,
                  self.mmbutton)
        self.Bind(wx.EVT_TOGGLEBUTTON, self.OnArbButtonClick,
                  self.arbbutton)
        
        h_sizer.Add(self.freqspin)
        h_sizer.Add(self.startbut)
        h_sizer.Add(self.arbbutton)
        h_sizer.Add(self.mmbutton)
        sizer.Add(h_sizer)

        self.SetSizer(sizer)
        self.Layout()

    def AddUpdateStrat(self):
        print self.pmodel.bdaqmid, self.pmodel.bfmid
        self.ustrat = updatestrategy.\
                      UpdateStrategy(bdaqmids = [self.pmodel.bdaqmid],
                                     bfmids = [self.pmodel.bfmid])
        
        # set update tick frequency to match selection
        updatetick = self.freqspin.GetValue()
        setattr(self.ustrat, managers.UTICK, updatetick)
        wx.GetApp().stratgroup.add(self.ustrat)
        self.pmodel.ustrat = self.ustrat

    def RemoveUpdateStrat(self):
        wx.GetApp().stratgroup.remove(self.ustrat)
        self.pmodel.ustrat = None

    def OnStartButtonClick(self, event):
        """Called when the start button is clicked."""

        pressed = self.IsStartButtonPressed()
        self.SetStartButtonLabelColor(pressed)

        if pressed:
            # enable mm and arb buttons
            self.mmbutton.Enable()
            self.arbbutton.Enable()
            # we add an update strategy to the global strategy group,
            self.AddUpdateStrat()
                
            # start the timer running
#            print 'timer set to {0}'.format(self.freqspin.GetValue())
#            self.timer.Start(self.freqspin.GetValue() * const.TICK_LENGTH_MS)
        else:
            self.RemoveUpdateStrat()
 #           if self.timer.IsRunning():
                # this will stop the price model being updated, and
                # therefore also the arb and mm models.
 #               self.timer.Stop()

            self.mmbutton.SetValue(False)
            self.arbbutton.SetValue(False)
            # disable mm and arb buttons; this changes their
            # appearance so that they don't look like they can be
            # clicked.
            self.mmbutton.Disable()
            self.arbbutton.Disable()

    def IsStartButtonPressed(self):
        """
        Convenience function for determining whether the start button
        is pressed.
        """

        return self.startbut.GetValue()

    def OnArbButtonClick(self, event):
        """Called when the arb button is clicked."""

        if self.arbbutton.GetValue():
            if self.IsStartButtonPressed():            
                # the pricing model will now update the arbmodel
                self.pmodel.AddListener(self.arbmodel.Update)
        else:
            self.pmodel.RemoveListener(self.arbmodel.Update)

    def OnMarketMakingButtonClick(self, event):
        """Called when the market making button is clicked."""

        if self.mmbutton.GetValue():
            # the pricing model will now update the mm model
            if self.IsStartButtonPressed():                
                self.pmodel.AddListener(self.mmmodel.Update)
        else:
            self.pmodel.RemoveListener(self.mmmodel.Update)

    def SetStartButtonLabelColor(self, pressed):
        if pressed:
            self.startbut.SetBackgroundColour('red')
            self.startbut.SetLabel('Stop')
        else:
            self.startbut.SetBackgroundColour('green')
            self.startbut.SetLabel('Start')

    def OnUpdateSpinCtrl(self, event):
        """Allow changing update frequency if timer is running."""

        # alter frequency for update strategy
        setattr(self.ustrat, managers.UTICK, self.freqspin.GetValue())        

#        if self.timer.IsRunning():
#            self.timer.Stop()
#            self.timer.Start(self.freqspin.GetValue() * 1000)

    #def OnTimerEvent(self, event):
        
        # update the price model (get the BF and BDAQ prices).  This
        # will update the view (prices shown in GUI) via listener
        # function.
    #    self.pmodel.Update()

    def StopUpdatesIfRunning(self):
        """Called when control panel is hidden."""

        # set the start button to off, then call the normal event
        # handler.
        self.startbut.SetValue(False)
        self.OnStartButtonClick(None)

        # clear the arb and mm strategies; this means that when we
        # navigate to a new market, we won't have residual strategies
        # from the old market that try to update.
        self.mmmodel.Clear()
        self.arbmodel.Clear()
