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
