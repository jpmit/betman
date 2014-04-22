"""Classes that will force the stores to update information.

Currently used for updating matching markets and matching selections.

New information is obtained using the BF/BDAQ API.  At the moment
these classes are used to forcibly refresh data for a particular Event
(get the available markets) and Market (get selection data).

"""

from betman.all.singleton import Singleton
from betman.core import stores
import updaterfunctions

@Singleton
class MatchSelectionUpdater(object):
    def __init__(self):
        self._mstore = stores.MatchMarketStore.Instance()
        self._sstore = stores.MatchSelectionStore.Instance()

    def update_selection_information(self, bdaqmid):
        bfmid = self._mstore.get_BFmid_from_BDAQmid(bdaqmid)
        
        bdaqsels, bfsels = updaterfunctions.get_ordered_selections(bdaqmid, bfmid)
        self._sstore.add_matching_selections(bdaqmid, bdaqsels, bfsels)

        return bdaqsels, bfsels

@Singleton
class MatchMarketUpdater(object):
    def __init__(self):
        self._mstore = stores.MatchMarketStore.Instance()

    def update_market_information(self, ename):
        mmarks = updaterfunctions.get_matching_markets(ename)
        self._mstore.add_matching_markets(ename, mmarks)

        return mmarks
