# bfnonapimethod.py
# James Mithen
# jamesmithen@gmail.com
#
# Web scraping functionality to replace certain annoying parts of the
# BF API.

from betman import *
import bfapiparse
import bfnonapiparse
import urllib2
import datetime
from betman.all import betlog

# for australia markets, replace uk with aus
BASEURL = ('http://uk-api.betfair.com/www/sports/exchange/readonly/'
           'v1.0/bymarket?currencyCode=GBP&alt=json&locale=en_GB')

def example():
    exampleurl = ('http://uk-api.betfair.com/www/sports/exchange/readonly'
                  '/v1.0/bymarket?currencyCode=GBP'
                  '&alt=xml&locale=en_GB&types=MARKET_STATE%2CMARKET_RATES'
                  '%2CMARKET_DESCRIPTION%2CEVENT%2'
                  'CRUNNER_DESCRIPTION%2CRUNNER_STATE%2C'
                  'RUNNER_EXCHANGE_PRICES_BEST%2CRUNNER_METADATA'
                  '&marketIds=1.110190866%2C1.110196550%2C1.110190863%2C'
                  '1.110190862%2C1.110190817'
                  '%2C1.110190864%2C1.110190829%2C1.110190830&ts=1374668724549')
    response = urllib2.urlopen(exampleurl)
    html = response.read()
    return html

def formula1():
    mid = 107586578
    alltypes = ['MARKET_STATE', # is it in play, in running etc
                'MARKET_RATES', # commission rates
                'MARKET_DESCRIPTION', #  market name and some other info
                'EVENT', # the event description (e.g. Formula 1)
                'RUNNER_DESCRIPTION',  # runner ids and names
                'RUNNER_STATE', # whether runners are active or not
                'RUNNER_EXCHANGE_PRICES_BEST', # selection ids and prices (top 3 only)
                'RUNNER_METADATA' # runnerid (not sure why I would need this
                ]
    typeswanted = ['MARKET_STATE']
    url = BASEURL + ('&types={0}'
                     '&marketIds=1.{1}'.format('%2C'.join(typeswanted),mid))
    print url

class nonAPIgetMarket(object):
    def __init__(self, urlclient, dbman):
        self.client = urlclient
        self.dbman = dbman
        self.setinput()

    def call(self, mids):
        allemids = []
        MAXMIDS = 50
        allminfo = []        
        for ids in util.chunks(mids, MAXMIDS):
            # for australian markets, need to write 2. rather than 1.  And
            # need different BASEURL (see top)
            midstring= '%2C'.join(['{0}.{1}'.format(self.client.mprefix,
                                                    m) for m in ids])
            url = self.client.pricesurl + ('&types=MARKET_STATE%2C'
                                           'MARKET_DESCRIPTION'
                                           '&marketIds={0}'.\
                                           format(midstring))

            betlog.betlog.debug('BF getMarket URL: {0}'.format(url))

            # make the HTTP request
            betlog.betlog.info('calling BF nonAPI getMarket')            
            response = self.client.call(url)

            # selections for all the market ids
            minfo = bfnonapiparse.ParsenonAPIgetMarket(response.read(),
                                                       mids)
            allminfo = allminfo + minfo

        return allminfo

class nonAPIgetSelections(object):
    def __init__(self, urlclient, dbman):
        self.client = urlclient
        self.dbman = dbman
        self.setinput()

    def setinput(self):
        pass
    
    def call(self, mids):
        """markets should be list of market ids AND
        markets should be all from the same event and either AUS or UK exchange.
        Otherwise, all hell will break loose...
        """
        # unsure what MAXMIDS should be.  BF returns HTTP 400 return
        # code if we ask for too much data, so try limiting to 50
        # market ids
        MAXMIDS = 50
        allselections = []
        allemids = []
        for ids in util.chunks(mids, MAXMIDS):
            # for australian markets, need to write 2. rather than 1.  And
            # need different BASEURL (see top)
            midstring= '%2C'.join(['{0}.{1}'.format(self.client.mprefix,
                                                    m) for m in ids])
            url = self.client.pricesurl + ('&types=RUNNER_DESCRIPTION%2CRUNNER_EXCHANGE'
                                           '_PRICES_BEST'
                                           '&marketIds={0}'.format(midstring))

            betlog.betlog.debug('BF Selection URL: {0}'.format(url))

            # make the HTTP request
            betlog.betlog.info('calling BF nonAPI getSelections')            
            response = self.client.call(url)

            # selections for all the market ids
            selections, emids = bfnonapiparse.ParseJsonSelections(response.read(), ids)
            allselections = allselections + selections
            allemids = allemids + emids
            
        if const.WRITEDB:
            # collapse list of lists to a flat list
            writeselections = [i for sub in allselections for i in sub]
            # write current time as timestamp for now!
            self.dbman.WriteSelections(writeselections, datetime.datetime.now())
        return allselections, allemids
