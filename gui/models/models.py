"""Models used in MVC style for the GUI."""

from operator import itemgetter
from betman.gui import guifunctions
from betman.core import stores, managers
from betman.strategy import strategy, cxstrategy, mmstrategy, position
from betman import const, exchangedata, database, order
from betman.all.singleton import Singleton
import numpy as np
import datetime

class AbstractModel(object):
    """
    Modified version from Robin Dunn's book, page 137.  Used as a base
    class for the other models below, used in the MVC design.
    """

    def __init__(self):
        self.listeners = []

    def AddListener(self, listenerf):
        self.listeners.append(listenerf)

    def RemoveListener(self, listenerf):
        self.listeners.remove(listenerf)

    def Update(self):
        """
        Update the information in the model, from DB/BDAQ API etc.
        """

        # note this function should be overloaded; this line is simply
        # indicating that the overloaded function should normally call
        # UpdateViews before returning.
        self.UpdateViews()

    def UpdateViews(self):
        """
        Execute all the listener functions, thus updating the views.
        """
        
        for eachf in self.listeners:
            eachf(self)

@Singleton
class OrderModel(AbstractModel):
    """Model for displaying live orders (see livebetsframe.py)."""

    def __init__(self):
        AbstractModel.__init__(self)

        # dictionary mapping the orefs of the live orders we are
        # interested in to order objects.  This is useful since we can
        # get rid of settled/voided/cancelled orders when updated if
        # we don't want to view them in the panel (just like BDAQ
        # does).
        self._lorders = []

        self._neworders = []

    def Update(self, ostore):
        # see if any of the orders we are currently tracking were
        # updated on the last tick
        updated = ostore.latest_updates

        # dicts of orders that were cancelled, updated, or newly
        # placed using the API.
        cords, uords, newords = ostore.latest

        # remove/update orders I currently hold.
        torem = []
        for i, o in enumerate(self._lorders):
            oref = o.oref
            exid = o.exid
            if oref in cords[exid]:
                o.status = order.CANCELLED
                o._DRAW = True
                torem.append(i)
            if oref in updated[exid]:
                newo = updated[exid][oref]
                newo._DRAW = True
                # might need to add a few more things from the old
                # order object
                self._lorders[i] = newo
            if oref in uords[exid]:
                newo = uords[oref]
                newo._DRAW = True
                # might need to add a few more things from the old
                # order object
                self._lorders[i] = newo
        
        #torem.reverse()
        #for i in torem:
        #    self._lorders.pop(i)

        # add new orders.
        self._neworders = []
        if newords:
            self._neworders = []
            for o in newords[const.BDAQID].values() + newords[const.BFID].values():
                self._neworders.append(o)
            # new orders appear at start of list
            self._lorders = self._lorders + self._neworders

        if (cords or uords or newords or updated[const.BDAQID] or updated[const.BFID]):
            self.UpdateViews()

    # def HaveMadeOrders(self):
    #     """Have we made any orders since starting the application?"""

    #     return bool(self._ostore.get_current_orders(const.BDAQID) or
    #                 self._ostore.get_current_orders(const.BFID))

    # def GetBDAQOrders(self):
    #     """Return dict of BDAQ orders."""

    #     return self._ostore.get_current_orders(const.BDAQID)

    # def GetBFOrders(self):
    #     """Return dict of BF orders."""

    #     return self._ostore.get_current_orders(const.BFID)

@Singleton
class PriceModel(AbstractModel):

    """
    Model used for displaying market prices on the main panel.  The
    model currently manages only a single market id, with the main
    pricepanel view in mind.

    The model is linked to an 'UpdateStrategy', which means that the
    application will automatically collect new market prices.  This
    class needs to do some bookkeeping so that the view looks okay,
    e.g. it needs to store the ordering of the selections.
    """
    
    def __init__(self):
        # we can't use super(PriceModel, self).__init__() here.
        AbstractModel.__init__(self)

        # sels are updated to keep the current selection prices; they
        # are stored in the order displayed on the main pricing panel.
        self._bdaqsels = []
        self._bfsels = []

        self._mstore = stores.MarketStore.Instance()
        self._sstore = stores.SelectionStore.Instance()

        # We set these once the user has clicked on a matching market.
        self._bdaqmid = None
        self._bfmid = None

    def SetBDAQMid(self, bdaqmid):
        self._bdaqmid = bdaqmid
        self._bfmid = self._mstore.get_BFmid_from_BDAQmid(bdaqmid)

    def GetMids(self):
        return self._bdaqmid, self._bfmid

    def SetSels(self, refresh=False):
        """Initialize selections in the correct display order."""

        # try getting the selections from the selection store
        self._bdaqsels, self._bfsels = self._sstore.\
                                       get_matching_selections(self._bdaqmid)

        if (not self._bdaqsels) or (refresh):
            # call BDAQ and BF api to get selections
            bfmid = self._mstore.get_BFmid_from_BDAQmid(self._bdaqmid)
            self._bdaqsels, self._bfsels = guifunctions.\
                                           market_prices(self._bdaqmid, bfmid)
            # write this back to the selection store.
            self._sstore.add_matching_selections(self._bdaqmid, self._bdaqsels,
                                                 self._bfsels)

        # store mapping of BDAQ selection name to index into sel list
        self._selindx = dict([(s.name, i) for (i, s) in enumerate(self._bdaqsels)])

    def GetSelsByBDAQName(self, bdaqname):
        """
        Return the particular BDAQ and BF selection objects with a
        certain BDAQ name.
        """

        indx = self._selindx[bdaqname]

        return self._bdaqsels[indx], self._bfsels[indx]

    def GetSels(self):
        """Return lists bdaqsels, bfsels."""

        return self._bdaqsels, self._bfsels

    def Update(self, prices):
        """
        Check if we need to update any views this tick, and update if
        we need to.
        """
        
        if self._bdaqmid != None:
            # check that we got new prices for this selection this tick.
            if (self._bdaqmid in prices[const.BDAQID] and
                self._bfmid in prices[const.BFID]):
                self._bdaqsels = [prices[const.BDAQID][self._bdaqmid][i]
                                 for i in [s.id for s in self._bdaqsels]]
                self._bfsels = [prices[const.BFID][self._bfmid][i]
                               for i in [s.id for s in self._bfsels]]

                # call the listener functions.
                self.UpdateViews()

@Singleton
class MatchMarketsModel(AbstractModel):
    """Model used for the matching markets view.

    Note the model is responsible for filtering the matching markets,
    e.g. so that we don't display historical markets in the matching
    markets panel.

    """
    
    # if usedb is set, we will initialise the matching markets cache
    # from the sqlite database.
    USEDB = True
    
    def __init__(self):

        AbstractModel.__init__(self)

        # the market store holds the actual data about markets
        self.mstore = stores.MarketStore.Instance()

        # we simply need to keep track of the event name, e.g. 'Horse
        # Racing' and a mapping between indices of data on the list
        # control, and the (BDAQ) market id.
        self._ename = ''
        self._bdaqmids = []

    def Update(self, ename, refresh=False):
        """
        Fetch matching markets for a particular event name.  If
        refresh is True, update the matching markets first by using
        the BDAQ and BF APIs.
        """

        if refresh:
            # use BDAQ and BF api to get list of matching markets
            self._mmarks = guifunctions.match_markets(ename)
            self.mstore.add_matching_markets(ename, self._mmarks)
        else:
            self._mmarks = self.mstore.get_matches(ename)

        # remove matching markets that don't concern the view
        # (e.g. historical markets).
        self._FilterMMarks()

        self._ename = ename
        self._bdaqmids = [m.id for m in [n[0] for n in self._mmarks]]

        # update should call the function that updates the view
        self.UpdateViews()

    def _FilterMMarks(self):
        """Remove matching markets that started > than 1 hour ago."""

        to_remove = []
        tplus1 = datetime.datetime.now() - datetime.timedelta(hours=1)

        for (i, (m1, m2)) in enumerate(self._mmarks):
            if (m1.starttime < tplus1):
                to_remove.append(i)

        to_remove.reverse()
        for i in to_remove:
            self._mmarks.pop(i)

    def GetBDAQMid(self, index):
        """Return bdaqmid corresponding to an index."""

        return self._bdaqmids[index]

    def GetEventName(self):
        return self._ename

# not a singleton as we want multiple instances
class StrategyModel(AbstractModel):
    """Holds information for a single strategy."""

    def __init__(self, bdaqsel, bfsel):
        super(StrategyModel, self).__init__() 

        # may not need this (?)
        self.bdaqselname = bdaqsel.name

        # the strategy model holds a strategy object, and a position
        # tracker, both of which are set to None if no strategy is
        # running.
        self.strategy = None
        self.postracker = None

        # messages from the strategy
        self.visited_states = []

        # length of self.visited_states
        self._nvisited = 0

        # string name of strategy in the GUI (see pricepanel.py),
        # e.g. 'Make BDAQ'
        self._string = None

    def GetStringSelection(self):
        """Get name of strategy as seen in GUI."""

        return self._string

    def InitStrategy(self, sname, strategy):
        """Add an actual strategy to the model.

        Currently this can be either a cross exchange (arb) strategy,
        or a market making strategy.
        """

        self._string = sname

        self.strategy = strategy
        self.postracker = position.PositionTracker(self.strategy)

    def RemoveStrategy(self):
        """Remove existing strategy from the model."""

        self.strategy = None
        self.postracker = None

    def HasStrategy(self):
        if self.strategy == None:
            return False
        return True

    def UpdateFrequency(self, newfreq):
        """Update the strategy frequency."""

        if self.strategy:
            setattr(self.strategy, managers.UTICK, newfreq)

    def Update(self, prices):
        # check that there is an underlying strategy, and that it was
        # updated in the last tick
        if self.strategy is not None:
            self.new_states = [] # reset
            if getattr(self.strategy, managers.UPDATED):
                # note we have to do it this way since the strategy
                # could have visited multiple states in a single
                # update.
                nvisited = self.strategy.brain.get_num_visited_states()
                if nvisited != self._nvisited:
                    self.visited_states = self.strategy.\
                                          brain.get_visited_states()
                    # the 'new_states' is accessed by the view
                    self.new_states = self.visited_states[self._nvisited:]
                    self._nvisited = nvisited

                self.UpdateViews()

# not a singleton as we want multiple instances
class GraphPriceModel(AbstractModel):
    """Holds information for a single graph."""
    
    NPOINTS = 100
    COMMISSION = cxstrategy._COMMISSION
    
    def __init__(self, bdaqsel, bfsel):
        super(GraphPriceModel, self).__init__()

        self.bdaqselname = bdaqsel.name

        # store mid and sid for both BDAQ and BF
        self.bdaqmid = bdaqsel.mid
        self.bfmid = bfsel.mid
        self.bdaqsid = bdaqsel.id
        self.bfsid = bfsel.id

        # store best back and lay prices on bdaq and bf
        self.bdaqback = [None]*self.NPOINTS
        self.bdaqlay = [None]*self.NPOINTS
        self.bfback = [None]*self.NPOINTS
        self.bflay = [None]*self.NPOINTS

        # store indexes (time points) of any (instant) arbitrage
        # opportunities.
        self.arbs = np.array([], dtype='int')

    def IsInstantArb(self, bdaqsel, bfsel):
        "TODO - this code replicates the code in cxstrategy.py"

        for (s1, s2) in [(bdaqsel, bfsel), (bfsel, bdaqsel)]:
            olay = s1.best_lay()

            if olay == exchangedata.MINODDS:
                # no lay price is currently offered
                return False

            # back selection at best current price
            oback = s2.best_back()

            if oback == exchangedata.MAXODDS:
                # no back price is currently offered
                return False

            if (oback > olay / ((1.0 - self.COMMISSION[const.BDAQID])*\
                                (1.0 - self.COMMISSION[const.BFID]))):
                #print 'arb!', self.bdaqselname, oback, olay
                return True
        return False

    def Update(self, prices):

        # check that we got new prices for this selection this tick.
        if (self.bdaqmid in prices[const.BDAQID] and
            self.bfmid in prices[const.BFID]):
            bdaqsel = prices[const.BDAQID][self.bdaqmid][self.bdaqsid]
            bfsel = prices[const.BFID][self.bfmid][self.bfsid]

            # get rid of the oldest data
            self.bdaqback.pop(0)
            self.bdaqlay.pop(0)
            self.bfback.pop(0)
            self.bflay.pop(0)

            # replace with new data
            self.bdaqback.append(bdaqsel.padback[0][0])
            self.bdaqlay.append(bdaqsel.padlay[0][0])
            self.bfback.append(bfsel.padback[0][0])
            self.bflay.append(bfsel.padlay[0][0])
            
            narbs = len(self.arbs)
            if narbs:
                # shift any existing arb opportunities to the previous
                # time point and remove at timepoints < 0
                self.arbs -= 1
                i = 0
                while (i < narbs and self.arbs[i] < 0):
                    i += 1
                self.arbs = self.arbs[i:]
                
            # check if latest data gives arb opportunity
            if self.IsInstantArb(bdaqsel, bfsel):
                # add final point to arb list
                self.arbs = np.append(self.arbs, self.NPOINTS - 1)

            # update the views
            self.UpdateViews()
