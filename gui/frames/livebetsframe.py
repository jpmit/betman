import wx
import sys
from wx.lib.agw import ultimatelistctrl as Ulc
from models import OrderModel
from betman.core import stores
from betman import const, order
import models

class LiveBetsFrame(wx.Frame):
    """Frame to view live bets, like the bottom panel on the BetDaq website."""

    def __init__(self, parent):
        wx.Frame.__init__(self, parent, size=(1200, 200), 
                          title='Live Bets')

        psizer = wx.BoxSizer(wx.HORIZONTAL)
        self._bpanel = LiveBetsPanel(self)
        psizer.Add(self._bpanel, 1, wx.EXPAND | wx.ALL | wx.ALIGN_CENTER)

        omodel = OrderModel.Instance()

        omodel.AddListener(self._bpanel.lst.OnNewOrderInformation)
        omodel.UpdateViews()

        self.SetSizer(psizer)

    def RemoveListeners(self):
        omodel = OrderModel.Instance()
        omodel.RemoveListener(self._bpanel.lst.OnNewOrderInformation)

class LiveBetsPanel(wx.Panel):
    def __init__(self, parent, *args, **kwargs):
        super(LiveBetsPanel, self).__init__(parent, *args, **kwargs)

        sizer = wx.BoxSizer(wx.VERTICAL)

        self.lst = BetListCtrl(self)

        sizer.Add(self.lst, 1, wx.EXPAND | wx.ALL | wx.ALIGN_CENTER)

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
        self.mstore = stores.MarketStore.Instance()

        # we use this model to map sids to selection names
        self.sstore = stores.SelectionStore.Instance()

        # dict mapping item number to order object
        self._curords = {}
        
        # for debug
        self._called = False

        self._parent = parent

    def _GetNumCurrentItems(self):
        return len(self._curords)

    def _AddNewOrderItems(self, olist):

        # shift the old order indices by number of new orders
        #self._curords = {k + len(olist) : v for (k, v) in self._curords.items()}
        
        ncur = self._GetNumCurrentItems()
        i = ncur
        for o in olist:
            # internal tracking
            self._curords[i] = o
            self._AddNewOrderItem(sys.maxint)
            i += 1

#        print self._mainWin._lines
#        print self._curords
#        self.RefreshItems(0, len(self._curords))
#        self.Refresh()
#        self.OnInternalIdle()
        #self._mainWin.RefreshLines(0, len(self._curords))
        #self._mainWin.OnPaint(None)

    def _AddNewOrderItem(self, indx):
        i = self.InsertStringItem(indx, "")
        print i, indx
        self._DrawOrderItem(i)

    def _DrawOrderItem(self, i):
        """Add order item to the list control in index indx."""
        
        # get the order object from internal tracker
        o = self._curords[i]

        COLOURS = {0: wx.BLACK, # not placed
                   1: wx.RED,   # unmatched
                   2: wx.GREEN, # matched
                   3: wx.BLACK, # cancelled
                   4: wx.WHITE  # settled
                   }
        status = order.STATUS_MAP[o.status]
        polarity = order.POLARITY_MAP[o.polarity]
        odds = o.price
        unmatched = o.unmatchedstake
        matched = o.matchedstake
        # note we use BDAQ name for both market and selection
        mname = _short_mname(self.mstore.get_BDAQname_from_mid(o.exid, o.mid))
        sname = self.sstore.get_BDAQ_name(o.exid, o.mid, o.sid)
        item = ("", "", status, mname, polarity, sname, odds,
                unmatched, matched, "", "")
        self.SetStringItem(i, 2, status)
        self.SetStringItem(i, 3, mname)
        self.SetStringItem(i, 4, polarity)
        self.SetStringItem(i, 5, sname)
        self.SetStringItem(i, 6, '{:.2f}'.format(odds))
        self.SetStringItem(i, 7, '{:.2f}'.format(unmatched))
        self.SetStringItem(i, 8, '{:.2f}'.format(matched))
        i2 = self.GetItem(i, 1)
        i2.SetMask(Ulc.ULC_MASK_BACKCOLOUR)
        i2.SetBackgroundColour(COLOURS[o.status])
        self.SetItem(i2)

    def OnNewOrderInformation(self, omodel):
        print "refresh order information!"
       
        #bdaqors = ostore.get_current_orders(const.BDAQID).values()
        # testors = [order.Order(1, 21410664, 0.5, 5.4, 1, **{'unmatchedstake': 0.5,
        #                                                     'matchedstake': 0.7,
        #                                                     'status': 1,
        #                                                     'mid': 3885853}),
        #            order.Order(2, 3166570, 1.04, 1.41, 2, **{'unmatchedstake': 3.21,
        #                                                      'matchedstake': 0.0,
        #                                                      'status': 2,
        #                                                      'mid': 113058412}),
        #            order.Order(2, 3166570, 1.04, 1.41, 2, **{'unmatchedstake': 3.21,
        #                                                      'matchedstake': 0.0,
        #                                                      'status': 2,
        #                                                      'mid': 113058412}),
        #            order.Order(2, 3166570, 1.04, 1.41, 2, **{'unmatchedstake': 3.21,
        #                                                      'matchedstake': 0.0,
        #                                                      'status': 2,
        #                                                      'mid': 113058412})]

        if not omodel._lorders:
            return

        # new orders
        neword = omodel._neworders
        nnew = len(neword)

        # add any new orders
        print 'neworders', neword
        if nnew:
            # this is what we really want to do
            self._AddNewOrderItems(neword)

        # modify / delete existing orders: we modify orders whose
        # status has changed in some way, and delete orders whose
        # status is 'CANCELLED' or 'SETTLED'.
        allors = omodel._lorders
        nors = len(allors)

        # we may need add all these orders as if they were new orders.
        if len(self._curords) != nors:
            self._AddNewOrderItems(allors)
        else:
            for i in range(0, nors - nnew):
                curo = self._curords[i]
                newo = allors[i]
                # check if something changed and, if so, update order
                if self._OrderChanged(curo, newo):
                    self._curords[i] = newo
                    self._DrawOrderItem(i)
        
        self.SetColumnWidth(0, wx.LIST_AUTOSIZE)
        self.Layout()
        self._parent.Layout()

    def _OrderChanged(self, co, no):
        if ((co.status != no.status) or (co.unmatchedstake != no.unmatchedstake)
            or (co.matchedstake != no.matchedstake)):
            return True
        return False
