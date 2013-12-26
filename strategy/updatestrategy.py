# updatestrategy.py
# James Mithen
# jamesmithen@gmail.com

"""
Update strategy which only exists to update prices, and does not
produce any bets.
"""

from betman import const
from betman.strategy import strategy

class UpdateStrategy(strategy.Strategy):
    """
    Allows updating an arbitrary number of BDAQ strategies and BF
    strategies.
    """
    
    def __init__(self, bdaqmids = [], bfmids = []):
        self.bdaqmids = bdaqmids
        self.bfmids = bfmids

        # we store a prices dict for this strategy, since we couple it
        # with the pricing model in the GUI.
        self.prices = {const.BDAQID: {}, const.BFID: {}}

    def get_marketids(self):
        return {const.BDAQID: self.bdaqmids, const.BFID: self.bfmids}

    def add_mids(self, middict):
        """Add additional mids."""

        bdmids = middict.get(const.BDAQID, [])
        bfmids = middict.get(const.BFID, [])

        self.bdaqmids += bdmids
        self.bfmids += bfmids

    def update(self, prices):
        self.prices = prices

    def remove_mids(self, middict):
        """Remove mids."""

        # note these will raise ValueError if we try to remove
        # non-existent mid.
        for bdmid in middict.get(const.BDAQID, []):
            self.bdaqmids.remove(bdmid)

        for bfmid in middict.get(const.BFID, []):
            self.bfmids.remove(bfmid)
