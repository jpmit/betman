"""Classes that will force the stores to update information.

New information is obtained using the BF/BDAQ API.  At the moment
these classes are used to forcibly refresh data for a particular Event
(get the available markets) and Market (get selection data).  Some of
the GUI models do this type of thing, but these classes are needed
since we may need to do this outside of the GUI.

"""

from betman.all.singleton import Singleton
from betman.core import stores
from betman.gui import guifunctions

@Singleton
class SelectionUpdater(object):
    def __init__(self):
        self._mstore = stores.MarketStore.Instance()
        self._sstore = stores.SelectionStore.Instance()

    def update_selection_information(self, bdaqmid):
        bfmid = self._mstore.get_BFmid_from_BDAQmid(bdaqmid)
        
        bdaqsels, bfsels = guifunctions.market_prices(bdaqmid, bfmid)
        self._sstore.add_matching_selections(bdaqmid, bdaqsels, bfsels)

@Singleton
class MarketUpdater(object):
    def __init__(self):
        self._mstore = stores.MarketStore.Instance()

    def update_market_information(self, ename):
        mmarks = guifunctions.match_markets(ename)
        self._mstore.add_matching_markets(ename, mmarks)
