from suds.client import Client
from suds.sax.element import Element
from betman import *

class BDAQClient(object):
    # mapping from my names to the WSDL info
    # syntactic sugar
    _READONLY = 'readonly'    
    _SECURE = 'secure'
    _sdict = {_READONLY: ['ReadOnlyService', 0],
              _SECURE: ['SecureService', 1]}
    def __init__(self, name):
        anames = BDAQClient._sdict.keys()
        if name not in anames:
            raise IOError('BDAQClient name must be one of: %s'
                          %(' '.join(anames)))
        self.name = name
        self.snum = BDAQClient._sdict[self.name][1]
        self.client = self._CreateSudsClient()

    def _CreateSudsClient(self):
        """Return SUDS client for BDAQ API"""
        client = Client(const.WSDLLOCAL['BDAQ'])
        client.set_options(service= BDAQClient._sdict[self.name][0],
                           headers={'user-agent': const.USERAGENT})
        # this SOAP header is required by the API in this form
        header = Element('ExternalApiHeader')
        if self.name == _READONLY:
            # we send only the username in the SOAP header
            astring = ('version="%s" currency="GBP" languageCode="en" '
                       'username="%s" '
                       'xmlns="http://www.GlobalBettingExchange'
                       '.com/ExternalAPI/"' %(const.BDAQAPIVERSION,
                                              const.BDAQUSER))
        if self.name == _SECURE:
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

class BFClient(object):
    # mapping from my names to the WSDL info    
    _sdict = {'global': [],
              'uk': [],
              'aus': []}
    def __init__(self, name):
        anames = BFClient._sdict.keys()
        if name not in anames:
            raise IOError('BFClient name must be one of: %s'
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
