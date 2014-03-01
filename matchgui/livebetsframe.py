import wx
from wx.lib.agw import ultimatelistctrl as Ulc
from models import OrderModel
from stores import OrderStore
from betman import const, order
import models

class LiveBetsFrame(wx.Frame):
    """Frame to view live bets, like the bottom panel on the BetDaq website."""

    def __init__(self, parent):
        wx.Frame.__init__(self, parent, size=(1200, 200), 
                          title='Live Bets')


        psizer = wx.BoxSizer(wx.HORIZONTAL)
        bpanel = LiveBetsPanel(self)
        psizer.Add(bpanel, 1, wx.EXPAND | wx.ALL | wx.ALIGN_CENTER)

        omodel = OrderModel.Instance()

        omodel.AddListener(bpanel.lst.OnNewOrderInformation)
        omodel.UpdateViews()

        self.SetSizer(psizer)

class LiveBetsPanel(wx.Panel):
    def __init__(self, parent, *args, **kwargs):
        super(LiveBetsPanel, self).__init__(parent, *args, **kwargs)

        sizer = wx.BoxSizer(wx.VERTICAL)

        self.lst = BetListCtrl(self)

        sizer.Add(self.lst, 0, wx.EXPAND | wx.ALL | wx.ALIGN_CENTER)

        self.SetSizer(sizer)

# functions for the listctrl display
def _short_mname(bdaqname):
    # this matches the BDAQ market name on the 'Live Bets' panel
    sp = bdaqname.split('|')
    return '{0} - {1}'.format(sp[-2], sp[-1])

class BetListCtrl(Ulc.UltimateListCtrl):
    """List bets."""

    def __init__(self, parent):
        super(BetListCtrl, self).__init__(parent, style=wx.LC_REPORT, 
                                          agwStyle=Ulc.ULC_HRULES | Ulc.ULC_REPORT)

        # add column headings
        self.InsertColumn(0, "")
        self.InsertColumn(1, "")
        self.InsertColumn(2, "Status")
        self.InsertColumn(3, "Market Name")
        self.InsertColumn(4, "Polarity")
        self.InsertColumn(5, "Selection")
        self.InsertColumn(6, "Odds")
        self.InsertColumn(7, "Unmatched")
        self.InsertColumn(8, "Matched")
        self.InsertColumn(9, "Matched Avg")
        self.InsertColumn(10, "Cancel")

        self.SetColumnWidth(0, 1)
        self.SetColumnWidth(1, 10)
        self.SetColumnWidth(2, 100)
        self.SetColumnWidth(3, 200)
        self.SetColumnWidth(4, 100)
        self.SetColumnWidth(5, 200)
        self.SetColumnWidth(6, 70)
        self.SetColumnWidth(7, 70)

        # we use this model to map mids to market names
        self.mmodel = models.MatchMarketsModel.Instance()

        # we use this model to map sids to selection names
        self.smodel = models.MatchSelectionsModel.Instance()

    def OnNewOrderInformation(self, omodel):
        print "refresh order information!"
       
        #bdaqors = ostore.get_current_orders(const.BDAQID).values()
        testors = [order.Order(1, 21410664, 0.5, 5.4, 1, **{'unmatchedstake': 0.5,
                                                            'matchedstake': 0.7,
                                                            'status': 1,
                                                            'mid': 3885853}),
                   order.Order(2, 3166570, 1.04, 1.41, 2, **{'unmatchedstake': 3.21,
                                                             'matchedstake': 0.0,
                                                             'status': 2,
                                                             'mid': 113058412}),
                   order.Order(2, 3166570, 1.04, 1.41, 2, **{'unmatchedstake': 3.21,
                                                             'matchedstake': 0.0,
                                                             'status': 2,
                                                             'mid': 113058412}),
                   order.Order(2, 3166570, 1.04, 1.41, 2, **{'unmatchedstake': 3.21,
                                                             'matchedstake': 0.0,
                                                             'status': 2,
                                                             'mid': 113058412})]

        COLOURS = {0: wx.BLACK,
                   1: wx.RED,
                   2: wx.GREEN}

        # get rid of all existing items on the ListCtrl
        self.DeleteAllItems()

        currors = omodel._lorders
        print 'current orders to draw', currors
        currors.reverse()
        allors = testors + currors

        for (i, o) in enumerate(allors):
            status = order.STATUS_MAP[o.status]
            polarity = order.POLARITY_MAP[o.polarity]
            odds = o.price
            unmatched = o.unmatchedstake
            matched = o.matchedstake
            # note we use BDAQ name for both market and selection
            mname = _short_mname(self.mmodel.GetBDAQNameFromMid(o.exid, o.mid))
            sname = self.smodel.GetBDAQName(o.exid, o.mid, o.sid)
            item = ("", "", status, mname, polarity, sname, odds,
                    unmatched, matched, "", "")
            self.Append(item)
#            i1 = self.GetItem(i, 0)
#            i1.SetBackgroundColour(COLOURS[o.status])
            i2 = self.GetItem(i, 1)
            i2.SetMask(Ulc.ULC_MASK_BACKCOLOUR)
            i2.SetBackgroundColour(COLOURS[o.status])
            self.SetItem(i2)
#            i2.SetBackgroundColour(COLOURS[o.status])
#            self.SetItem(i1)
#            self.SetItem(i2)
            
        
        self.SetColumnWidth(0, wx.LIST_AUTOSIZE)
           
        self.Layout()
