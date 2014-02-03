# bdaqnonapimethod.py
# James Mithen
# jamesmithen@gmail.com

"""
Web scraping functionality to replace certain annoying parts of the
BDAQ Api.
"""

import bdaqnonapiparse
import datetime
from betman import const, util, betlog
from betman.api.apimethod import NonApiMethod

class NonApiGetPrices(NonApiMethod):
    """
    Replacement for ApiGetPrices, which is throttled when using the
    BDAQ API.
    """
    
    def __init__(self, urlclient, dbman):
        super(NonApiGetPrices, self).__init__(urlclient)
        self.dbman = dbman
    
    def call(self, mids, writedb = False):
        """
        mids should be list of market ids.

        Note that by default we don't write selection information to
        the database.  This is because for multithreaded applications
        writing to the DB asynchronously is problematic (as well as a
        bit time consuming).
        """

        # unsure what MAXMIDS should be.  BDAQ returns HTTP 400 return
        # code if we ask for too much data, so try limiting to 50
        # market ids.
        MAXMIDS = 50
        allselections = {}
        allemids = []
        for ids in util.chunks(mids, MAXMIDS):

            midstring= '&mid=' + '&mid='.join(['{0}'.format(m) for m in ids])
            url = self.client.pricesurl + midstring + '&ccyCode=GBP'

            betlog.betlog.info('calling BDAQ nonApi GetPrices')
            betlog.betlog.debug('BDAQ Selection URL: {0}'.format(url))

            # make the HTTP request
            response = self.client.call(url)

            # selections for all the market ids
            selections, emids = bdaqnonapiparse.\
                                ParseNonApiGetPrices(response.read(),
                                                     ids)
            allselections.update(selections)
            allemids = allemids + emids

        if writedb:
            # get single flat list of selection objects from dict of dicts
            sels = [m.values() for m in allselections.values()]
            allsels = [item for subl in sels for item in subl]
            self.dbman.WriteSelections(allsels, datetime.datetime.now())

        # return selection dictionary and the list of erroneous market ids
        return allselections, allemids
