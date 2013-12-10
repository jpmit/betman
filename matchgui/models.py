import matchguifunctions

class AbstractModel(object):
    """Modified version from Robin Dunn's book, page 137."""

    def __init__(self):
        self.listeners = []

    def AddListener(self, listenerFunc):
        self.listeners.append(listenerFunc)

    def RemoveListener(self, listenerFunc):
        self.listeners.remove(listenerFunc)

    def Update(self):
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

    def SetPrices(self):
        """Use the BDAQ and BF apis to refresh the prices."""
        
        print 'called the event'
        self.bdaqsels, self.bfsels = matchguifunctions.\
                                     market_prices(self.event,
                                                   self.index)
        self.indexdict = {s.name : i for (i,s) in enumerate(self.bdaqsels)}
        
        # update should call the function that updates the view
        self.Update()

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

        print 'updating the model'
        
        if ename not in self.match_cache:
            # code to set match cache
            self.match_cache[ename] = matchguifunctions.match_markets(ename)

        # update should call the function that updates the view
        self.Update()

    def GetMatches(self, ename):
        return self.match_cache[ename]

class GraphPriceModel(AbstractModel):
    NPOINTS = 100
    def __init__(self, bdaqselname):
        super(GraphPriceModel, self).__init__()

        self.bdaqselname = bdaqselname

        # store best back and lay prices on bdaq and bf
        self.bdaqback = [None]*GraphPriceModel.NPOINTS
        self.bdaqlay = [None]*GraphPriceModel.NPOINTS
        self.bfback = [None]*GraphPriceModel.NPOINTS
        self.bflay = [None]*GraphPriceModel.NPOINTS

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
