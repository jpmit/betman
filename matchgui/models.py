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
        #self.addListener(self.print_something)
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
        
        # update should call the function that updates the GUI
        self.Update()
