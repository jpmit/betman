import wx
import const
from betman import const as bconst
from betman import order

class MonitorFrame(wx.Frame):
    def __init__(self, key):
        wx.Frame.__init__(self, None,
                          title='Strategy monitor for {0}'\
                          .format(key), size=(800, 400))

        # store key, this is used so that we can track when the frame
        # is killed
        self.key = key

        panel_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.summary_panel = SummaryPanel(self)
        self.state_panel = StatePanel(self)
        self.bets_panel = BetsPanel(self)

        panel_sizer.Add(self.summary_panel, 1, wx.EXPAND | wx.RIGHT, 5)
        panel_sizer.Add(self.state_panel, 1, wx.EXPAND | wx.ALL, 5)
        panel_sizer.Add(self.bets_panel, 1, wx.EXPAND | wx.LEFT, 5)

        self.SetSizer(panel_sizer)

    def OnUpdateStrat(self, smodel):
        """Update the view using the StrategyModel smodel."""

        # propagate the update to each of the panels
        self.summary_panel.Update(smodel)
        self.state_panel.Update(smodel)
        self.bets_panel.Update(smodel)

class SummaryPanel(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent)

        main_sizer = wx.BoxSizer(wx.VERTICAL)
        pos_sizer = wx.BoxSizer(wx.HORIZONTAL)
        posif_sizer = wx.BoxSizer(wx.HORIZONTAL)

        self.position = 0.0
        self.unmatched_bets = []
        self.position_if = 0.0

        self.position_text = wx.StaticText(self)
        pos_sizer.Add(wx.StaticText(self, label = 'position:  '))
        pos_sizer.Add(self.position_text)

        self.posif_text = wx.StaticText(self)
        posif_sizer.Add(wx.StaticText(self, label = 'position if:  '))
        posif_sizer.Add(self.posif_text)

        main_sizer.AddSpacer(20)
        main_sizer.Add(pos_sizer)
        main_sizer.Add(posif_sizer)
        main_sizer.AddSpacer(40)
        main_sizer.Add(wx.StaticText(self, label = 'unmatched bets:  '))
        self.bets_sizer = wx.BoxSizer(wx.VERTICAL)
        main_sizer.Add(self.bets_sizer)

        # draw text
        self.DrawPositionIfText()
        self.DrawPositionText()

        self.SetSizer(main_sizer)
        self.Layout()

    def DrawUnmatchedBets(self):
        self.bets_sizer.Clear()

        for o in self.unmatched_bets:
            bsz = wx.BoxSizer(wx.HORIZONTAL)
            bsz.Add(wx.StaticText(self, label = 'BDAQ' if o.exid == bconst.BDAQID else 'BF'))
            bsz.AddSpacer(20)
            bsz.Add(wx.StaticText(self, label = 'back' if o.polarity == order.BACK else 'lay'))
            bsz.AddSpacer(20)
            bsz.Add(wx.StaticText(self, label = '{:.2f}'.format(o.price)))
            bsz.AddSpacer(20)
            bsz.Add(wx.StaticText(self, label = '{:.2f}'.format(o.matchedstake)))
            bsz.AddSpacer(20)            
            bsz.Add(wx.StaticText(self, label = '{:.2f}'.format(o.unmatchedstake)))
            self.bets_sizer.Add(bsz)
        self.Layout()

    def DrawPositionText(self):
        if self.position == 0.0:
            col = const.BLACK
        elif self.position > 0.0:
            col = const.GREEN
        else:
            col = const.RED

        self.position_text.SetLabel('{:.2f}'.format(self.position))
        self.position_text.SetForegroundColour(col)

    def DrawPositionIfText(self):
        if self.position_if == 0.0:
            col = const.BLACK
        elif self.position_if > 0.0:
            col = const.GREEN
        else:
            col = const.RED

        self.posif_text.SetLabel('{:.2f}'.format(self.position_if))
        self.posif_text.SetForegroundColour(col)        
        
    def Update(self, smodel):

        if smodel.postracker is None:
            # we could get here on the first update
            return

        pos, posif = smodel.postracker.get_positions()

        # check if position, position_if, and unmatched_bets have
        # changed, and update the panel to reflect this if so.

        if pos != self.position:
            self.position = pos
            self.DrawPositionText()
        if posif != self.position_if:
            self.position_if = posif
            self.DrawPositionIfText()

        unmatched = smodel.postracker.get_unmatched_bets()

        if unmatched != self.unmatched_bets:
            self.unmatched_bets = unmatched
            self.DrawUnmatchedBets()

class BetsPanel(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent)

        self.all_bets = []

        self.bets_sizer = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(self.bets_sizer)
        self.Layout()

    def DrawBets(self):
        """Draw info for all bets made thus far."""
        
        self.bets_sizer.Clear()

        for o in self.all_bets:
            bsz = wx.BoxSizer(wx.HORIZONTAL)
            bsz.Add(wx.StaticText(self, label = 'BDAQ' if o.exid == bconst.BDAQID else 'BF'))
            bsz.AddSpacer(20)
            bsz.Add(wx.StaticText(self, label = 'back' if o.polarity == order.BACK else 'lay'))
            bsz.AddSpacer(20)
            bsz.Add(wx.StaticText(self, label = '{:.2f}'.format(o.price)))
            bsz.AddSpacer(20)
            bsz.Add(wx.StaticText(self, label = '{:.2f}'.format(o.matchedstake)))
            bsz.AddSpacer(20)            
            bsz.Add(wx.StaticText(self, label = '{:.2f}'.format(o.unmatchedstake)))
            self.bets_sizer.Add(bsz)
        self.Layout()
        
    def Update(self, smodel):

        all_bets = smodel.postracker.get_all_bets()

        # todo: this comparison is inefficient
        if self.all_bets != all_bets:
            self.all_bets = all_bets
            self.DrawBets()

class StatePanel(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent)

        self.txtctrl = wx.TextCtrl(self, style=wx.TE_READONLY | wx.TE_MULTILINE | wx.TE_DONTWRAP)
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.sizer.Add(self.txtctrl, 1, wx.LEFT | wx.TOP | wx.GROW)
        self.SetSizer(self.sizer)
        self.Fit()

        # write some initial message
        self.txtctrl.AppendText('States visited:\n')

        # do we have some state information written on the frame.
        self._somestates = False

    def Update(self, smodel):

        # add information on visited states to txtctrl
        if not self._somestates:
            # first time this has been called, get all the visited
            # states and write to the txtcontrol.
            statelist = smodel.visited_states
            self._somestates = True
        else:
            # get new states since last call, and append to the txtcontrol.
            statelist = smodel.new_states
        if statelist:
            self.txtctrl.AppendText('\n'.join(statelist) + '\n')
