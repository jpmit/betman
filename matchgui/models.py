from operator import itemgetter
import matchguifunctions
from betman.strategy import strategy, cxstrategy, mmstrategy, position
from betman import const, exchangedata
from betman.database import DBMaster
from betman.matchmarkets.matchconst import EVENTMAP
from singleton import Singleton
import managers
import numpy as np

class AbstractModel(object):
    """
    Modified version from Robin Dunn's book, page 137.  Used as a base
    class for the other models below, used in the MVC design.
    """

    def __init__(self):
        self.listeners = []

    def AddListener(self, listenerFunc):
        self.listeners.append(listenerFunc)

    def RemoveListener(self, listenerFunc):
        self.listeners.remove(listenerFunc)

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
        
        for eachFunc in self.listeners:
            eachFunc(self)

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
        self.bdaqsels = []
        self.bfsels = []

        # we store a reference to a matching selections model, which
        # gives us details on which BF selection matches which BDAQ
        # selection.
        self._selmodel = MatchSelectionsModel.Instance()

        # We set these once the user has clicked on a matching market.
        self.bdaqmid = None
        self.bfmid = None

    def SetMids(self, bdaqmid, bfmid):
        self.bdaqmid = bdaqmid
        self.bfmid = bfmid

    def SetSels(self, refresh = False):
        """Initialize selections in the correct order."""

        # this may call the BDAQ API
        self.bdaqsels, self.bfsels = self._selmodel.\
                                     GetMatchingSels(self.bdaqmid,
                                                     self.bfmid)

        # indexdict means that the price of a particular bdaq
        # selection name can be easily found.
        self.indexdict = {s.name : i for (i, s) in enumerate(self.bdaqsels)}

    def GetSelsByBDAQName(self, bdaqname):
        """
        Return the particular BDAQ and BF selection objects with a
        certain BDAQ name.
        """

        indx = self.indexdict[bdaqname]

        return self.bdaqsels[indx], self.bfsels[indx]

    def GetSels(self):
        """Return lists bdaqsels, bfsels."""

        return self.bdaqsels, self.bfsels

    def Update(self, prices):
        """
        Check if we need to update any views this tick, and update if
        we need to.
        """
        
        if self.bdaqmid != None:
            # check that we got new prices for this selection this tick.
            if (self.bdaqmid in prices[const.BDAQID] and
                self.bfmid in prices[const.BFID]):
                self.bdaqsels = [prices[const.BDAQID][self.bdaqmid][i]
                                 for i in [s.id for s in self.bdaqsels]]
                self.bfsels = [prices[const.BFID][self.bfmid][i]
                               for i in [s.id for s in self.bfsels]]

                # call the listener functions.
                self.UpdateViews()

@Singleton
class MatchSelectionsModel(AbstractModel):
    """Stores data on matching selections for all the different events."""
    
    # if usedb is set, we will initialise the matching markets cache
    # from the sqlite database.
    USEDB = True
    
    def __init__(self):
        
        AbstractModel.__init__(self)
        #super(MatchSelectionsModel, self).__init__()

        # matching selections keys are bdaqmid, values are
        # [(bdaq_sels, bf_sels)] where bdaq_sels and bf_sels are lists
        # of bdaq and bf selections, ordered as displayed on the BDAQ
        # website.  Instead of dumping everything from the DB into the
        # cache immediately, we add to the cache 'as needed'.
        self._match_cache = {}

        # singleton that controls DB access
        self._dbman = DBMaster()

    def GetMatchingSels(self, bdaqmid, bfmid, refresh = False):
        """
        Return lists bdaqsels, bfsels, where bdaqsels[i] is the
        selection that matches bfsels[i], and the ordering of the
        selections is that given by the BDAQ display order.

        We call the BDAQ and BF api to get this information if
        necessary.
        """

        callapi = False # don't refresh prices using BDAQ/BF API
                        # unless necessary.
        if refresh:
            callapi = True
        else:
            if bdaqmid in self._match_cache:
                bdaqsels, bfsels = self._match_cache[bdaqmid]
            else:
                # try filling up the cache from the DB
                msels = self._dbman.ReturnSelectionMatches([bdaqmid])

                if msels:
                    bdaqsels, bfsels = [itemgetter(0)(i) for i in msels],\
                                       [itemgetter(1)(i) for i in msels]
                    # check that display order is not None
                    if bdaqsels[0].dorder is None:
                        callapi = True
                else:
                    # didn't find any matching selections in DB
                    callapi = True

        if callapi:
            # call BDAQ and BF api to get selections, and store in
            # local cache.
            bdaqsels, bfsels = matchguifunctions.\
                               market_prices(bdaqmid, bfmid)

        # put entries into match cache.
        self._match_cache[bdaqmid] = (bdaqsels, bfsels)

        return bdaqsels, bfsels

@Singleton
class MatchMarketsModel(AbstractModel):
    """Stores data on matching markets for all the different events."""
    
    # if usedb is set, we will initialise the matching markets cache
    # from the sqlite database.
    USEDB = True
    
    def __init__(self):

        AbstractModel.__init__(self)
        #super(MatchMarketsModel, self).__init__()

        # key to match_cache is event name, value is list of tuples
        # (m1, m2) where m1 and m2 are the matching markets (m1 is the
        # BDAQ market, m2 is the BF market.  The ordering of the
        # tuples is the same as the ordering that appears in the GUI.
        self._match_cache = {}

        # store a dict that maps BDAQ mids to BF mids
        self._BDAQmap_cache = {}

        # and a dict that maps BF mids to BDAQ mids
        self._BFmap_cache = {}

        # and a dict that maps BDAQ mids to their market objects
        self._BDAQ_cache = {}

        # and a dict that maps BF mids to their market objects
        self._BF_cache = {}

        # singleton that controls DB access
        self._dbman = DBMaster()

        if self.USEDB:
            self.InitCachesFromDB()
        else:
            self.InitCachesEmpty()

    def InitCachesEmpty(self):
        """
        Initialise the matching markets cache as empty.
        """
        
        for ename in EVENTMAP:
            self._match_cache[ename] = []
            # the other caches are set to be empty after __init__

    def GetMids(self, ename, index):
        bdaqmid = self._match_cache[ename][index][0].id
        bfmid = self._match_cache[ename][index][1].id
        
        return bdaqmid, bfmid

    def GetBFMidFromBDAQMid(self, bdaqmid):
        return self._BDAQmap_cache[bdaqmid]

    def GetBDAQMidFromBFMid(self, bfmid):
        return self._BFmap_cache[bfmid]

    def GetNameFromBDAQMid(self, bdaqmid):
        return self._BDAQ_cache[bdaqmid].name

    def InitCachesFromDB(self):
        """
        Initialise the matching markets cache from the SQLite
        database.
        """

        for ename in EVENTMAP:
            mmarks = self._dbman.ReturnMarketMatches([ename])
            self.SetCaches(ename, mmarks)

    def SetCaches(self, ename, mmarks):
        # ordered list of matching markets for event ename
        self._match_cache[ename] = mmarks

        for m1, m2 in mmarks:
            m1id = m1.id
            m2id = m2.id
            # map bdaq mid to bf mid
            self._BDAQmap_cache[m1id] = m2id

            # map bf mid to bdaq mid
            self._BFmap_cache[m2id] = m1id

            # map bdaq mid to market object
            self._BDAQ_cache[m1id] = m1

            # map bf mid to market object
            self._BF_cache[m2id] = m2

    def GetMarketName(self, ename, index):
        """
        Return market name for particular event with particular index.
        """
        
        return self._match_cache[ename][index][0].name

    def Update(self, ename, refresh=False):
        """
        Fetch matching markets for a particular event name.  If
        refresh is True, update the matching markets first by using
        the BDAQ and BF APIs.
        """

        if refresh:
            # code to set match cache; note this will automatically
            # save the details to the DB.
            mmarks = matchguifunctions.match_markets(ename)
            self.SetCaches(ename, mmarks)

        # update should call the function that updates the view
        self.UpdateViews()

    def GetMatches(self, ename):
        return self._match_cache[ename]

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
        # we provide
        # new_states - 
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
