# apiclient.py
# James Mithen
# jamesmithen@gmail.com
#

"""
Clients used in calling API functions for both BDAQ and Betfair.  Also
clients used in calling non-API (web-scraping) functions for both BDAQ
and Betfair.
"""

from suds.client import Client
from suds.sax.element import Element
from betman import const
import urllib2

class BDAQAPIClient(object):
    # mapping from my names to the WSDL info
    # syntactic sugar
    _READONLY = 'readonly'    
    _SECURE = 'secure'
    _sdict = {_READONLY: ['ReadOnlyService', 0],
              _SECURE: ['SecureService', 1]}
    def __init__(self, name):
        anames = BDAQAPIClient._sdict.keys()
        if name not in anames:
            raise IOError('BDAQAPIClient name must be one of: %s'
                          %(' '.join(anames)))
        self.name = name
        self.snum = BDAQAPIClient._sdict[self.name][1]
        self.client = self._CreateSudsClient()

    def _CreateSudsClient(self):
        """Return SUDS client for BDAQ API"""
        client = Client(const.WSDLLOCAL['BDAQ'])
        client.set_options(service= BDAQAPIClient._sdict[self.name][0],
                           headers={'user-agent': const.USERAGENT})
        # this SOAP header is required by the API in this form
        header = Element('ExternalApiHeader')
        if self.name == BDAQAPIClient._READONLY:
            # we send only the username in the SOAP header
            astring = ('version="%s" currency="GBP" languageCode="en" '
                       'username="%s" '
                       'xmlns="http://www.GlobalBettingExchange'
                       '.com/ExternalAPI/"' %(const.BDAQAPIVERSION,
                                              const.BDAQUSER))
        if self.name == BDAQAPIClient._SECURE:
            # we send the username and password in the SOAP header
            astring = ('version="%s" currency="GBP" languageCode="en" '
                       'username="%s" password="%s" '
                       'xmlns="http://www.GlobalBettingExchange'
                       '.com/ExternalAPI/"' %(const.BDAQAPIVERSION,
                                              const.BDAQUSER,
                                              const.BDAQPASS))
        
        header.attributes = [astring]
        client.set_options(soapheaders=header)    
        return client

    def MethodNames(self):
        """Return list of methods (API functions)"""
        return self.client.wsdl.services[self.snum].ports[0].methods.keys()

    def __str__(self):
        """Print names of methods (API functions)"""

class BDAQnonAPIClient(object):
    def __init__(self):
        # this is the 'base' URL got getting the prices.  We can add
        # other 'base' URLs here for different functionality.
        self.pricesurl = 'http://www.betdaq.com/UI/3.57/MDC/PPMarkets.aspx?'

        # headers for http requests
        self.headers = { 'User-Agent' : const.USERAGENT }

    def call(self, url):
        req = urllib2.Request(url, headers=self.headers)
        return urllib2.urlopen(req)

class BFAPIClient(object):
    # mapping from my names to the WSDL info    
    _sdict = {'global': [],
              'uk': [],
              'aus': []}
    def __init__(self, name):
        anames = BFAPIClient._sdict.keys()
        if name not in anames:
            raise IOError('BFAPIClient name must be one of: %s'
                          %(' '.join(anames)))
        self.name = name
        self.client = self._CreateSudsClient()

    def _CreateSudsClient(self):
        """Return SUDS client for BDAQ API"""
        client = Client(const.WSDLLOCAL['BF' + self.name])
        client.set_options(headers={'user-agent': const.USERAGENT})
        return client

    def MethodNames(self):
        """Return list of methods (API functions)"""
        return self.client.wsdl.services[self.snum].ports[0].methods.keys()

    def SetReqHead(self, rhead):
        """Set request header, which contains the session token"""
        self.client.reqheader = rhead

class BFnonAPIClient(object):
    # mapping from names to the URL we want to call
    UK = 'uk'
    AUS = 'aus'
    _sdict = {UK : ('http://uk-api.betfair.com/www/sports/exchange/readonly/'
                      'v1.0/bymarket?currencyCode=GBP&alt=json&locale=en_GB'),
              AUS : ('http://aus-api.betfair.com/www/sports/exchange/readonly/'
                      'v1.0/bymarket?currencyCode=GBP&alt=json&locale=en_GB')}
    def __init__(self, name):
        anames = BFnonAPIClient._sdict.keys()
        if name not in anames:
            raise IOError('BFnonAPIClient name must be one of: %s'
                          %(' '.join(anames)))
        self.name = name
        # this is the 'base' URL got getting the prices.  We can add
        # other 'base' URLs here for different functionality.
        self.pricesurl = BFnonAPIClient._sdict[name]
        # the prefix is needed to get the prices of the markets
        self.mprefix = 1 if self.name == BFnonAPIClient.UK else 2
        # headers for http requests
        self.headers = { 'User-Agent' : const.USERAGENT }

    def call(self, url):
        req = urllib2.Request(url, headers=self.headers)
        return urllib2.urlopen(req)
