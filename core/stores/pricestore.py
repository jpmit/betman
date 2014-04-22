"""PriceStore.

This class does all the book-keeping for the price information.  It is
accessed by the PriceManager (see managers.py). It also handles
writing order and price information to the database.

"""

from betman import const
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

    def add_prices(self, prices):
        """Add prices to the store."""

        # we store the most recent prices in their own dict
        self.newprices = prices

        self._prices.update(prices)

        # write prices to database
        print 'prices from pricestore:'
        print prices

            # get single flat list of selection objects from dict of dicts
            #sels = [m.values() for m in allselections.values()]
            #allsels = [item for subl in sels for item in subl]
            #self.dbman.write_selections(allsels, datetime.datetime.now())
