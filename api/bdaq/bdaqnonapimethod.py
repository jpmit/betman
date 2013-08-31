# bdaqnonapimethod.py
# James Mithen
# jamesmithen@gmail.com
#
# Web scraping functionality to replace certain annoying parts of the
# BDAQ API.

from betman import const, util
import bdaqnonapiparse

class nonAPIGetPrices(object):
    def __init__(self, urlclient, dbman):
        self.client = urlclient
        self.dbman = dbman
        self.setinput()

    def setinput(self):
        pass
    
    def call(self, mids):
        """Get selections and prices for list of BDAQ market ids mids"""
        # unsure what MAXMIDS should be.  BF returns HTTP 400 return
        # code if we ask for too much data, so try limiting to 50
        # market ids
        MAXMIDS = 50
        allselections = []
        for ids in util.chunks(mids, MAXMIDS):
            # for australian markets, need to write 2. rather than 1.  And
            # need different BASEURL (see top)
            midstring= '&mid=' + '&mid='.join(['{0}'.format(m) for m in mids])
            url = self.client.pricesurl + midstring + '&ccyCode=GBP'
            if const.DEBUG:
                print 'BDAQ Selection URL: {0}'.format(url)

            # make the HTTP request
            response = self.client.call(url)

            if const.DEBUG:
                return bdaqnonapiparse.ParsenonAPIGetPrices(response.read(), ids)

            # selections for all the market ids
            selections = bdaqnonapiparse.ParsenonAPIGetPrices(response.read(), ids)
            allselections = allselections + selections
        if const.WRITEDB:
            # collapse list of lists to a flat list
            writeselections = [i for sub in allselections for i in sub]
            # write current time as timestamp for now!
            self.dbman.WriteSelections(writeselections, datetime.datetime.now())
        return allselections
