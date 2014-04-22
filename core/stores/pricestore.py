"""PriceStore.

This class does all the book-keeping for the price information.  It is
accessed by the PriceManager (see managers.py). It also handles
writing order and price information to the database.

"""

import datetime

from betman import const, database, util
from betman.all.singleton import Singleton

@Singleton
class PriceStore(object):
    def __init__(self):
        """Class for storing latest prices."""

        # current state of prices
        self._prices = {const.BDAQID: {}, const.BFID: {}}

        # note newprices is not 'private' since it is accessed by the
        # engine; it will be fed to the strategies.
        self.newprices = {const.BDAQID: {}, const.BFID: {}}

        # for writing to database
        self._dbman = database.DBMaster()

    def add_prices(self, prices):
        """Add prices to the store.

        Note this currently gets called by the PricingManager even
        when prices is {const.BDAQID: {}, const.BFID: {}} (i.e. no
        prices)

        """

        # we store the most recent prices in their own dict
        self.newprices = prices

        self._prices.update(prices)

        # write prices to database
        if prices[const.BDAQID] or prices[const.BFID]:
            bdaqsels = util.flattendict(prices[const.BDAQID])
            bfsels = util.flattendict(prices[const.BFID])
            self._dbman.write_selections(bdaqsels + bfsels, 
                                         datetime.datetime.now())
