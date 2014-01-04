import matchguifunctions
from betman.strategy import strategy, cxstrategy, mmstrategy
from betman import const
from betman.database import DBMaster
from betman.matchmarkets.matchconst import EVENTMAP
import managers

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
        super(PriceModel, self).__init__()
        # sels are updated to keep the current selection prices; they
        # are stored in the order displayed on the main pricing panel.
        self.bdaqsels = []
        self.bfsels = []
        self.event = None
        self.index = None

    def SetEventIndex(self, event, index):
        self.event = event
        self.index = index

    def SetMids(self, bdaqmid, bfmid):
        self.bdaqmid = bdaqmid
        self.bfmid = bfmid

    def InitSels(self):
        """Initialize selections in the correct order."""
        
        self.bdaqsels, self.bfsels = matchguifunctions.\
                                     market_prices(self.event,
                                                   self.index)

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
        if self.index != None:
            # check that we got new prices for this selection this tick.
            if self.bdaqmid in prices[const.BDAQID]:
                self.bdaqsels = [prices[const.BDAQID][self.bdaqmid][i]
                                 for i in [s.id for s in self.bdaqsels]]
                self.bfsels = [prices[const.BFID][self.bfmid][i]
                               for i in [s.id for s in self.bfsels]]

                # call the listener functions.
                self.UpdateViews()

class MarketMakingModel(AbstractModel):

    def __init__(self):
        super(MarketMakingModel, self).__init__()

        # the arbitrage model owns a group of strategies.  each
        # individual strategy involves a pair of selections.
        self.stratgroup = strategy.StrategyGroup()

    def Clear(self):
        self.stratgroup.clear()

    def InitStrategies(self, bdaqsels, bfsels):
        pass
        
    def Update(self, pmodel):
        print 'updating MM model'
        self.UpdateViews()

class ArbitrageModel(AbstractModel):

    def __init__(self):
        super(ArbitrageModel, self).__init__()

        # the arbitrage model owns a group of strategies.  each
        # individual strategy involves a pair of selections.
        self.stratgroup = strategy.StrategyGroup()

    def InitStrategies(self, bdaqsels, bfsels):
        for (bdsel, bfsel) in zip(bdaqsels, bfsels):
            self.stratgroup.add(cxstrategy.CXStrategy(bdsel, bfsel))

    def Update(self, pmodel):
        print 'updating Arb model'

        # we need to update the strategy group with a prices
        # dictionary.
        self.stratgroup.update(pmodel.PricesDict())
        # probably call the functionality to make bets somewhere
        # here...

        # progagate the updates
        self.UpdateViews()

    def Clear(self):
        self.stratgroup.clear()
    

class MatchMarketsModel(AbstractModel):
    """Stores data on matching markets for all the different events."""
    
    # if usedb is set, we will initialise the match cache from the
    # sqlite database.
    USEDB = True
    
    def __init__(self):
        super(MatchMarketsModel, self).__init__()

        # key to match_cache is event name, value is list of tuples
        # (m1, m2) where m1 and m2 are the matching markets (m1 is the
        # BDAQ market, m2 is the BF market.
        self._match_cache = {}

        # singleton that controls DB access
        self._dbman = DBMaster()

        if self.USEDB:
            self.InitMatchCacheFromDB()
        else:
            self.InitMatchCacheEmpty()

    def InitMatchCacheEmpty(self):
        """
        Initialise the matching markets cache as empty.
        """
        
        for ename in EVENTMAP:
            self._match_cache[ename] = []

    def GetMids(self, ename, index):
        bdaqmid = self._match_cache[ename][index][0].id
        bfmid = self._match_cache[ename][index][1].id
        
        return bdaqmid, bfmid

    def InitMatchCacheFromDB(self):
        """
        Initialise the matching markets cache from the SQLite
        database.
        """

        for ename in EVENTMAP:
            self._match_cache[ename] = self._dbman.\
                                       ReturnMarketMatches([ename])

        # set global cache in matchguifunctions to match this one
        matchguifunctions.set_match_cache(self._match_cache)

    def GetMarketName(self, ename, index):
        """
        Return market name for particular event with particular index.
        """
        
        return self._match_cache[ename][index][0].name

    def FetchMatches(self, ename, refresh = False):
        """
        Fetch matching markets for a particular event name.  If
        refresh is True, update the matching markets first by using
        the BDAQ and BF APIs.
        """

        if refresh:
            # code to set match cache; note this will automatically
            # save the details to the DB, providing WRITEDB = True in
            # code/betman/all/const.py.
            self._match_cache[ename] = matchguifunctions.\
                                       match_markets(ename)

        # update should call the function that updates the view
        self.UpdateViews()

    def GetMatches(self, ename):
        return self._match_cache[ename]

class StrategyModel(AbstractModel):
    """Holds information for a single strategy."""

    def __init__(self, bdaqsel, bfsel):
        super(StrategyModel, self).__init__() 

        # may not need this (?)
        self.bdaqselname = bdaqsel.name

        self.strategy = None

        # messages from the strategy
        self.messages = []

    def InitStrategy(self, strategy):
        """
        Add an actual strategy to the model.

        Currently this can be either a cross exchange (arb) strategy,
        or a market making strategy.
        """

        self.strategy = strategy

    def RemoveStrategy(self):
        """Remove existing strategy from the model."""

        self.strategy = None

    def HasStrategy(self):
        if self.strategy == None:
            return False
        return True

    def Update(self, prices):
        # check that there is an underlying strategy, and that it was
        # updated in the last tick
        if self.strategy is not None:
            if getattr(self.strategy, managers.UPDATED):
                # TODO: get a proper message from the strategy...
                self.messages.append('I updated the strategy!')

                self.UpdateViews()

class GraphPriceModel(AbstractModel):
    """Holds information for a single graph."""
    
    NPOINTS = 100
    
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

    def Update(self, prices):

        # check that we got new prices for this selection this tick.
        if self.bdaqmid in prices[const.BDAQID]:
            bdaqsel = prices[const.BDAQID][self.bdaqmid][self.bdaqsid]
            bfsel = prices[const.BFID][self.bfmid][self.bfsid]

            self.bdaqback.append(bdaqsel.padback[0][0])
            self.bdaqlay.append(bdaqsel.padlay[0][0])
            self.bfback.append(bfsel.padback[0][0])
            self.bflay.append(bfsel.padlay[0][0])

            # get rid of the oldest data
            self.bdaqback.pop(0)
            self.bdaqlay.pop(0)
            self.bfback.pop(0)
            self.bflay.pop(0)

            # update the views
            self.UpdateViews()
