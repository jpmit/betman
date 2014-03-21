# apiclient.py
# James Mithen
# jamesmithen@gmail.com

"""
Clients used in calling API functions for both BDAQ and Betfair.  Also
clients used in calling non-API (web-scraping) functions for both BDAQ
and Betfair.
"""

from suds.client import Client
from suds.sax.element import Element
from betman import const
import urllib2

class BDAQApiClient(object):
    """
    Client object to handle requests to the Betdaq Api.  This simply
    configures the Client object from the Suds library.  Instances
    comes in two flavors, if __init__ is called with 'secure' we have
    a client that for calling the 'secure' Api methods, if it is
    called with 'readonly' we have a client for calling the 'readonly'
    methods (see the BDAQ docs).  The difference between these two is
    that the secure client will send the password in SOAP requests,
    the readonly client will not.
    """
    
    # mapping from my names to the WSDL info
    _READONLY = 'readonly'    
    _SECURE   = 'secure'
    _sdict    = {_READONLY: ['ReadOnlyService', 0],
                 _SECURE:   ['SecureService', 1]}
    
    def __init__(self, service):
        """
        Create the SUDS client with the correct options and headers
        for the chosen service, which can be either 'readonly' or
        'secure'.
        """
        
        # allowed services
        aservices = BDAQApiClient._sdict.keys()
        if service not in aservices:
            raise IOError('service must be one of: {0}'.\
                          format(' '.join(aservices)))
        self.service = service
        self.snum = BDAQApiClient._sdict[self.service][1]
        # after this call, self.client will be a SUDS client object
        self._create_suds_client()

    def _create_suds_client(self):
        """Create SUDS client for BDAQ Api."""
        
        self.client = Client(const.WSDLLOCAL['BDAQ'])
        self.client.set_options(service = BDAQApiClient._sdict[self.service][0],
                                headers = {'user-agent': const.USERAGENT})

        # put username (and password if necessary) into the headers.
        # note that another way to do this is to call betdaq.set_user,
        # so the username and password in const.py do not need to be
        # specified.
        self.set_headers(const.BDAQUSER, const.BDAQPASS)

    def method_names(self):
        """Return list of methods (Api functions)"""
        
        return self.client.wsdl.services[self.snum].ports[0].methods.keys()

    def set_headers(self, name, password):
        """Set the username and password that needs to go in the SOAP header."""
           
        # this SOAP header is required by the Api in this form
        header = Element('ExternalApiHeader')
        
        if self.service == BDAQApiClient._READONLY:
            # we send the username only in the SOAP header
            astring = ('version="{0}" currency="GBP" languageCode="en" '
                       'username="{1}" '
                       'xmlns="http://www.GlobalBettingExchange'
                       '.com/ExternalAPI/"'.format(const.BDAQAPIVERSION,
                                                   name))
        if self.service == BDAQApiClient._SECURE:
            # we send the username and password in the SOAP header
            astring = ('version="{0}" currency="GBP" languageCode="en" '
                       'username="{1}" password="{2}" '
                       'xmlns="http://www.GlobalBettingExchange'
                       '.com/ExternalAPI/"'.format(const.BDAQAPIVERSION,
                                                   name,
                                                   password))
        # set header
        header.attributes = [astring]
        self.client.set_options(soapheaders = header)

class BDAQNonApiClient(object):
    """Client object to 'screen scrape' data from the Betdaq website."""

    def __init__(self):
        # this is the 'base' URL got getting the prices.  We can add
        # other 'base' URLs here for different functionality.
        self.pricesurl = ('http://www.betdaq.com/UI/3.65/MDC/PPMarkets'
                          '.aspx?')

        # headers for http requests
        self.headers = { 'User-Agent' : const.USERAGENT }

    def call(self, url):
        req = urllib2.Request(url, headers=self.headers)
        return urllib2.urlopen(req)

class BFApiClient(object):
    """Client object to handle requests to the Betfair Api."""
      
    # mapping from my names to the WSDL info    
    _sdict = {'global': [],
              'uk': [],
              'aus': []}
    def __init__(self, name):
        anames = BFApiClient._sdict.keys()
        if name not in anames:
            raise IOError('BFApiClient name must be one of: %s'
                          %(' '.join(anames)))
        self.name = name
        self.client = self._create_suds_client()

    def _create_suds_client(self):
        """Return SUDS client for BDAQ Api."""
        
        client = Client(const.WSDLLOCAL['BF' + self.name])
        client.set_options(headers={'user-agent': const.USERAGENT})
        return client

    def method_names(self):
        """Return list of methods (Api functions)."""
        
        return self.client.wsdl.services[self.snum].ports[0].methods.keys()

    def set_reqheader(self, rhead):
        """Set request header, which contains the session token"""
        self.client.reqheader = rhead

class BFNonApiClient(object):
    """Client object to 'screen scrape' data from the Betdaq website."""
    
    # mapping from names to the URL we want to call
    UK = 'uk'
    AUS = 'aus'
    # not too sure whether v1.0 could be replaced below
    _sdict = {UK : ('http://uk-api.betfair.com/www/sports/exchange/readonly/'
                      'v1.0/bymarket?currencyCode=GBP&alt=json&locale=en_GB'),
              AUS : ('http://aus-api.betfair.com/www/sports/exchange/readonly/'
                      'v1.0/bymarket?currencyCode=GBP&alt=json&locale=en_GB')}
    
    def __init__(self, name):
        """
        Set HTTP headers and prefix needed to choose between AUS
        and UK markets.
        """

        anames = BFNonApiClient._sdict.keys()
        if name not in anames:
            raise IOError('BFNonApiClient name must be one of: %s'
                          %(' '.join(anames)))
        self.name = name
        # this is the 'base' URL got getting the prices.  We can add
        # other 'base' URLs here for different functionality.
        self.pricesurl = BFNonApiClient._sdict[name]
        # the prefix is needed to get the prices of the markets
        self.mprefix = 1 if self.name == BFNonApiClient.UK else 2
        # headers for http requests
        self.headers = { 'User-Agent' : const.USERAGENT }

    def call(self, url):
        req = urllib2.Request(url, headers=self.headers)
        return urllib2.urlopen(req)
