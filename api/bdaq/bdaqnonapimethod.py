# bdaqnonapimethod.py
# James Mithen
# jamesmithen@gmail.com
#
# Web scraping functionality to replace certain annoying parts of the
# BDAQ API.

from betman import const, util
import bdaqnonapiparse
import datetime
from betman.all import betlog

class nonAPIGetPrices(object):
    def __init__(self, urlclient, dbman):
        self.client = urlclient
        self.dbman = dbman
        self.setinput()

    def setinput(self):
        pass
    
    def call(self, mids):
        """Get selections and prices for list of BDAQ market ids mids"""
        # unsure what MAXMIDS should be.  BDAQ returns HTTP 400 return
        # code if we ask for too much data, so try limiting to 50
        # market ids
        MAXMIDS = 50
        allselections = {}
        allemids = []
        for ids in util.chunks(mids, MAXMIDS):
            # for australian markets, need to write 2. rather than 1.  And
            # need different BASEURL (see top)
            midstring= '&mid=' + '&mid='.join(['{0}'.format(m) for m in ids])
            url = self.client.pricesurl + midstring + '&ccyCode=GBP'

            betlog.betlog.info('calling BDAQ nonAPI GetPrices')
            betlog.betlog.debug('BDAQ Selection URL: {0}'.format(url))

            # make the HTTP request
            response = self.client.call(url)

            # selections for all the market ids
            selections, emids = bdaqnonapiparse.\
                                ParsenonAPIGetPrices(response.read(),
                                                     ids)
            allselections.update(selections)
            allemids = allemids + emids

        # return list of selections and the list of erroneous market ids
        return allselections, allemids
