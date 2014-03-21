import wx
import sys
from wx.lib.agw import ultimatelistctrl as Ulc
from models import OrderModel
from betman.core import stores
from betman import const, order
import models

class LiveBetsFrame(wx.Frame):
    """Frame to view live bets, cf. bottom panel on the BetDaq website."""

    def __init__(self, parent):
        wx.Frame.__init__(self, parent, size=(1200, 200), 
                          title='Live Bets')

        psizer = wx.BoxSizer(wx.HORIZONTAL)
        self._bpanel = LiveBetsPanel(self)
        psizer.Add(self._bpanel, 1, wx.EXPAND|wx.ALL|wx.ALIGN_CENTER)

        # model for MVC
        omodel = OrderModel.Instance()
        omodel.AddListener(self._bpanel.lst.OnNewOrderInformation)

        # force initial update
        omodel.UpdateViews()

        self.SetSizer(psizer)

    def RemoveListeners(self):
        """Called when the frame is closed (destroyed).

        This ensures we don't try to push updates to a non-existent
        object.

        """

        omodel = OrderModel.Instance()
        omodel.RemoveListener(self._bpanel.lst.OnNewOrderInformation)

class LiveBetsPanel(wx.Panel):
    """Panel that contains the list widget."""

    def __init__(self, parent, *args, **kwargs):
        super(LiveBetsPanel, self).__init__(parent, *args, **kwargs)

        sizer = wx.BoxSizer(wx.VERTICAL)

        self.lst = BetListCtrl(self)

        sizer.Add(self.lst, 1, wx.EXPAND | wx.ALL | wx.ALIGN_CENTER)
        self.SetSizer(sizer)

def _short_mname(bdaqname):
    """Return short market name that appears in the list widget."""

    # this matches the BDAQ market name on the 'Live Bets' panel
    sp = bdaqname.split('|')
    return '{0} - {1}'.format(sp[-2], sp[-1])

class BetListCtrl(Ulc.UltimateListCtrl):
    """The list widget that displays the live bets."""

    # mapping of order status to color
    _COLOURS = {order.NOTPLACED: wx.BLACK,
                order.UNMATCHED: wx.RED,  
                order.MATCHED: wx.GREEN,
                order.CANCELLED: wx.BLACK,
                order.SETTLED: wx.Color(255, 255, 0)
                }

    # mapping of exchange id to name
    _EXNAME = {const.BDAQID: 'BDAQ',
               const.BFID: 'BF'
              }

    def __init__(self, parent):
        super(BetListCtrl, self).__init__(parent, style=wx.LC_REPORT, 
                                          agwStyle=Ulc.ULC_HRULES | Ulc.ULC_REPORT)

        # add column headings
        self.InsertColumn(0, "")
        self.InsertColumn(1, "")
        self.InsertColumn(2, "Exchange")
        self.InsertColumn(3, "Status")
        self.InsertColumn(4, "Market Name")
        self.InsertColumn(5, "Polarity")
        self.InsertColumn(6, "Selection")
        self.InsertColumn(7, "Odds")
        self.InsertColumn(8, "Unmatched")
        self.InsertColumn(9, "Matched")
        self.InsertColumn(10, "Matched Avg")
        self.InsertColumn(11, "Cancel")

        self.SetColumnWidth(0, 1)
        self.SetColumnWidth(1, 10)
        self.SetColumnWidth(2, 85)
        self.SetColumnWidth(3, 100)
        self.SetColumnWidth(4, 200)
        self.SetColumnWidth(5, 100)
        self.SetColumnWidth(6, 200)
        self.SetColumnWidth(7, 70)
        self.SetColumnWidth(8, 70)

        # used to map mids to market names
        self._mstore = stores.MatchMarketStore.Instance()

        # used to map sids to selection names
        self._sstore = stores.MatchSelectionStore.Instance()

        # dict mapping item number to order object
        self._curords = {}
        
        # for debug
        self._called = False

        self._parent = parent

    def _GetNumCurrentItems(self):
        """Return number of orders the widget currently tracks."""

        return len(self._curords)

    def _AddNewOrderItems(self, olist):
        """Add list of new order items to the widget.

        The new orders are added at the bottom of the list, in the
        order they are in olist, i.e. olist[-1] will appear at the
        very bottom, with olist[-2] above it, etc.

        """
        
        ncur = self._GetNumCurrentItems()
        i = ncur
        for o in olist:
            # _currords is for internal tracking
            self._curords[i] = o
            self._AddNewOrderItem(sys.maxint)
            i += 1

    def _AddNewOrderItem(self, indx):
        """Add new order item at index indx."""

        # i is the actual position at which the item has been
        # inserted, which should be equal to indx.
        i = self.InsertStringItem(indx, "")
        self._DrawOrderItem(i)

    def _DrawOrderItem(self, i):
        """Draw the order item currently at index i."""
        
        # get the order object from internal tracker
        o = self._curords[i]

        status = order.STATUS_MAP[o.status]
        polarity = order.POLARITY_MAP[o.polarity]
        odds = o.price
        unmatched = o.unmatchedstake
        matched = o.matchedstake
        # note we use BDAQ name for both market and selection
        mname = _short_mname(self._mstore.get_BDAQname_from_mid(o.exid, o.mid))
        sname = self._sstore.get_BDAQ_name(o.exid, o.mid, o.sid)

        # set the items
        self.SetStringItem(i, 2, self._EXNAME[o.exid])
        self.SetStringItem(i, 3, status)
        self.SetStringItem(i, 4, mname)
        self.SetStringItem(i, 5, polarity)
        self.SetStringItem(i, 6, sname)
        self.SetStringItem(i, 7, '{:.2f}'.format(odds))
        # abs since otherwise can appear as -0.0 in widget
        self.SetStringItem(i, 8, '{:.2f}'.format(abs(unmatched)))
        self.SetStringItem(i, 9, '{:.2f}'.format(abs(matched)))
        # draw the color as given by order status
        item = self.GetItem(i, 1)
        item.SetMask(Ulc.ULC_MASK_BACKCOLOUR)
        item.SetBackgroundColour(self._COLOURS[o.status])
        self.SetItem(item)

    def OnNewOrderInformation(self, omodel):

        # list of all orders
        allorders = omodel.GetLiveOrders()
        if not allorders:
            return
        nors = len(allorders)

        # new orders
        neworders = omodel.GetNewOrders()
        nnew = len(neworders)

        # add any new orders
        if nnew:
            print 'neworders', neworders
            self._AddNewOrderItems(neworders)

        if len(self._curords) != nors:
            # add all orders as if they were newly placed orders: we
            # arrive here if we have called this function for the
            # first time and we have already made some orders.
            self._AddNewOrderItems(allorders)
        else:
            # for all orders we are currently tracking, check if
            # something changed and, if so, redraw the item.
            for i in range(0, nors - nnew):
                curo = self._curords[i]
                newo = allorders[i]
                if self._OrderChanged(curo, newo):
                    self._curords[i] = newo
                    self._DrawOrderItem(i)

        # may or may not need these three lines
        self.SetColumnWidth(0, wx.LIST_AUTOSIZE)
        self.Layout()
        self._parent.Layout()

    def _OrderChanged(self, co, no):
        """Return True if order 'co' is different from order 'no', else False."""

        if ((co.status != no.status) or (co.unmatchedstake != no.unmatchedstake)
            or (co.matchedstake != no.matchedstake)):
            return True
        return False
