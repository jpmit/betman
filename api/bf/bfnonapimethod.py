# bfnonapimethod.py
# James Mithen
# jamesmithen@gmail.com

"""
Web scraping functionality to replace certain annoying parts of the BF
Api.
"""

import bfnonapiparse
import datetime
from betman import util, betlog
from betman.api.apimethod import NonApiMethod

def _example():
    """Example for testing."""
    import urllib2
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

def _formula1():
    """Example for testing."""
    
    BASEURL = ('http://uk-api.betfair.com/www/sports/exchange/readonly/'
               'v1.0/bymarket?currencyCode=GBP&alt=json&locale=en_GB')
    
    mid = 107586578
    alltypes = ['MARKET_STATE', # is it in play, in running etc
                'MARKET_RATES', # commission rates
                'MARKET_DESCRIPTION', #  market name and some other info
                'EVENT', # the event description (e.g. Formula 1)
                'RUNNER_DESCRIPTION',  # runner ids and names
                'RUNNER_STATE', # whether runners are active or not
                'RUNNER_EXCHANGE_PRICES_BEST', # selection ids and prices (top 3 only)
                'RUNNER_METADATA' # runnerid (not sure why I would need this)
                ]
    typeswanted = ['MARKET_STATE']
    url = BASEURL + ('&types={0}'
                     '&marketIds=1.{1}'.format('%2C'.join(typeswanted),mid))
    print url

class NonApigetMarket(NonApiMethod):
    """
    Get information about a market.  Replacement for ApigetMarket,
    which is badly throttled (5p/s) when using the free BF API.
    """
    
    def __init__(self, urlclient, dbman):
        super(NonApigetMarket, self).__init__(urlclient)
        self.dbman = dbman

    def call(self, mids):
        allemids = []
        MAXMIDS = 50
        allminfo = {}
        allemids = []
        for ids in util.chunks(mids, MAXMIDS):
            # for AUS markets, need to write 2. rather than 1. 
            midstring= '%2C'.join(['{0}.{1}'.format(self.client.mprefix,
                                                    m) for m in ids])

            # note also that pricesurl is diferent for UK and AUS markets.
            url = self.client.pricesurl + ('&types=MARKET_STATE%2C'
                                           'MARKET_DESCRIPTION'
                                           '&marketIds={0}'.\
                                           format(midstring))

            #betlog.betlog.debug('BF getMarket URL: {0}'.format(url))

            # make the HTTP request
            betlog.betlog.info('calling BF nonApi getMarket')            
            response = self.client.call(url)

            # selections for all the market ids
            minfo, emids = bfnonapiparse.ParsenonApigetMarket(response.read(),
                                                              mids)
            
            allminfo.update(minfo)
            allemids = allemids + emids
            
        return allminfo, allemids

class NonApigetPrices(NonApiMethod):
    """
    Replacement for ApigetPrices, which is throttled when using
    the BF free API.
    """
    
    def __init__(self, urlclient, dbman):
        super(NonApigetPrices, self).__init__(urlclient)
        self.dbman = dbman
    
    def call(self, mids):
        """
        mids should be list of market ids.
        """
        
        # unsure what MAXMIDS should be.  BF returns HTTP 400 return
        # code if we ask for too much data, so try limiting to 50
        # market ids for now (seems to work).
        MAXMIDS = 50
        allselections = {}
        allemids = []
        for ids in util.chunks(mids, MAXMIDS):
            
            # mprefix is 1 for UK markets and 2 for AUS markets
            midstring= '%2C'.join(['{0}.{1}'.format(self.client.mprefix,
                                                    m) for m in ids])
            url = self.client.pricesurl + ('&types=RUNNER_DESCRIPTION%2'
                                           'CRUNNER_EXCHANGE'
                                           '_PRICES_BEST'
                                           '&marketIds={0}'.format(midstring))

            betlog.betlog.debug('BF Selection URL: {0}'.format(url))

            # make the HTTP request
            betlog.betlog.info('calling BF nonApi getPrices')            
            response = self.client.call(url)

            # selections for all the market ids
            selections, emids = bfnonapiparse.\
                                ParseJsonSelections(response.read(),
                                                    ids)
 
            allselections.update(selections)
            allemids = allemids + emids

        return allselections, allemids
