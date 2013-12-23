import matchguifunctions
from betman.strategy import strategy, cxstrategy, mmstrategy
from betman import const

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
    
    def __init__(self):
        super(PriceModel, self).__init__()
        self.bdaqsels = []
        self.bfsels = []
        self.event = None
        self.index = None

    def SetEventIndex(self, event, index):
        self.event = event
        self.index = index

    def PricesDict(self):
        """Return prices dict that the strategies can use."""

        bdaqmid = self.bdaqsels[0].mid
        bfmid = self.bfsels[0].mid

        pdict = {const.BDAQID: {bdaqmid: {s.id : s for s in self.bdaqsels}},
                 const.BFID: {bfmid: {s.id : s for s in self.bfsels}}}

        return pdict

    def Update(self):
        """Use the BDAQ and BF apis to refresh the prices."""
        
        print 'called the event'
        self.bdaqsels, self.bfsels = matchguifunctions.\
                                     market_prices(self.event,
                                                   self.index)
        self.indexdict = {s.name : i for (i,s) in enumerate(self.bdaqsels)}
        
        # update should call the function that updates the view
        self.UpdateViews()

class MarketMakingModel(AbstractModel):

    def __init__(self):
        super(MarketMakingModel, self).__init__()

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

class MatchMarketsModel(AbstractModel):
    """Stores data on matching markets for all the different events."""
    
    def __init__(self):
        super(MatchMarketsModel, self).__init__()
        # key to match_cache is event name, value is list of tuples
        # (m1, m2) where m1 and m2 are the matching markets (m1 is the
        # BDAQ market, m2 is the BF market.
        self.match_cache = {}

    def FetchMatches(self, ename):
        """
        Fetch list of matching events for event ename. If not already
        cached, this will use the BF and BDAQ APIs.
        """
        
        if ename not in self.match_cache:
            # code to set match cache
            self.match_cache[ename] = matchguifunctions.\
                                      match_markets(ename)

        # update should call the function that updates the view
        self.UpdateViews()

    def GetMatches(self, ename):
        return self.match_cache[ename]

class GraphPriceModel(AbstractModel):
    NPOINTS = 100
    
    def __init__(self, bdaqselname):
        super(GraphPriceModel, self).__init__()

        self.bdaqselname = bdaqselname

        # store best back and lay prices on bdaq and bf
        self.bdaqback = [None]*self.NPOINTS
        self.bdaqlay = [None]*self.NPOINTS
        self.bfback = [None]*self.NPOINTS
        self.bflay = [None]*self.NPOINTS

    def UpdatePrices(self, pmodel):
        """This receives updates from the main price model above."""

        # This if statement allows us to keep graphs for particular
        # selections floating around, even if we have now used the GUI
        # to navigate to a new event...
        if self.bdaqselname not in pmodel.indexdict:
            return

        i = pmodel.indexdict[self.bdaqselname]

        # store latest price in the arrays
        bdaqsel = pmodel.bdaqsels[i]
        bfsel = pmodel.bfsels[i]
        self.bdaqback.append(bdaqsel.padback[0][0])
        self.bdaqlay.append(bdaqsel.padlay[0][0])
        self.bfback.append(bfsel.padback[0][0])
        self.bflay.append(bfsel.padlay[0][0])

        # get rid of the oldest data
        self.bdaqback.pop(0)
        self.bdaqlay.pop(0)
        self.bfback.pop(0)
        self.bflay.pop(0)

        # update should call the function that updates the GUI
        self.Update()
