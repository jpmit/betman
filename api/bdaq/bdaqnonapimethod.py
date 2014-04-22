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
    
    def __init__(self, urlclient):
        super(NonApiGetPrices, self).__init__(urlclient)
    
    def call(self, mids):
        """
        mids should be list of market ids.
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
#            betlog.betlog.debug('BDAQ Selection URL: {0}'.format(url))

            # make the HTTP request
            response = self.client.call(url)

            # selections for all the market ids
            selections, emids = bdaqnonapiparse.\
                                ParseNonApiGetPrices(response.read(),
                                                     ids)
            allselections.update(selections)
            allemids = allemids + emids

        # return selection dictionary and the list of erroneous market ids
        return allselections, allemids
