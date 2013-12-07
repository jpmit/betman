import wx
import models

class ControlPanel(wx.Panel):
    """Panel for setting market refresh rate, etc."""

    def __init__(self, parent, *args, **kwargs):
        super(ControlPanel, self).__init__(parent, *args, **kwargs)
        self.CreateLayout()

        self.timer = wx.Timer(self)
        self.pmodel = models.PriceModel()
        # when the model updates, we call the OnUpdatePrices method of
        # the PricePanel.
        ppanel = self.GetTopLevelParent().GetPricePanel()
#        event, index = ppanel.GetEventIndex()
#        self.pmodel.SetEventIndex(event, index)
        self.pmodel.AddListener(ppanel.OnUpdatePrices)
        self.Bind(wx.EVT_TIMER, self.OnTimerEvent)
        self.Bind(wx.EVT_SPINCTRL, self.OnUpdateSpinCtrl)

        # update prices on the pricepanel
        #ppanel.OnUpdatePrices(self.pmodel)
        
    def CreateLayout(self):
        sizer = wx.BoxSizer(wx.VERTICAL)
        h_sizer = wx.BoxSizer(wx.HORIZONTAL)

        self.freqspin = wx.SpinCtrl(self, -1, min = 1, max = 100)
        self.but = wx.ToggleButton(self)
        self.SetButtonLabelColor(False)
        
        h_sizer.Add(self.freqspin)
        h_sizer.Add(self.but)
        sizer.Add(h_sizer)

        self.Bind(wx.EVT_TOGGLEBUTTON, self.OnUpdateClick, self.but)

        self.SetSizer(sizer)
        self.Layout()

    def SetButtonLabelColor(self, pressed):
        if pressed:
            self.but.SetBackgroundColour('red')
            self.but.SetLabel('Stop')
        else:
            self.but.SetBackgroundColour('green')
            self.but.SetLabel('Start')

    def OnUpdateSpinCtrl(self, event):
        """Allow changing update frequency if timer is running."""
        
        if self.timer.IsRunning():
            self.timer.Stop()
            self.timer.Start(self.freqspin.GetValue() * 1000)

    def OnTimerEvent(self, event):
        # update the model (get the BF and BDAQ prices)
        self.pmodel.SetPrices()

    def StopTimerIfRunning(self):
        """Called when control panel is hidden."""
        
        if self.timer.IsRunning():
            self.timer.Stop()
            self.SetButtonLabelColor(False)
            # set button pushed status to False
            self.but.SetValue(False)

    def OnUpdateClick(self, event):

        isPressed = self.but.GetValue()
        self.SetButtonLabelColor(isPressed)

        if self.timer.IsRunning():
            self.timer.Stop()
        else:
            print 'timer set to {0}'.format(self.freqspin.GetValue())
            self.timer.Start(self.freqspin.GetValue() * 1000)
        
        print "start updates"
