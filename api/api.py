import suds
from suds.client import Client
from suds.sax.element import Element
import logging
logging.basicConfig(level=logging.INFO)
logging.getLogger('suds.client').setLevel(logging.DEBUG)
logging.getLogger('suds.transport').setLevel(logging.DEBUG)


wsdl = 'file:///home/jm0037/python/bdaq/API.wsdl'
client = Client(wsdl)
client.set_options(service="ReadOnlyService",headers={'user-agent':'pybetman/0.1 Python/ Suds %s' %suds.__version__})
client2 = Client(wsdl)
client2.set_options(service="SecureService")#,transport=suds.transport.https.HttpAuthenticated)
# add headers
ssn = Element('ExternalApiHeader')
astring = 'version="2" currency="GBP" languageCode="en" username="jimmybob" xmlns="http://www.GlobalBettingExchange.com/ExternalAPI/"'
ssn.attributes = [astring]
client.set_options(soapheaders=ssn)
client2.set_options(soapheaders=ssn)

r = client.factory.create('ListTopLevelEventsRequest')
r._WantPlayMarkets = False
result = client.service.ListTopLevelEvents(r)

r2 = client2.factory.create('GetAccountBalancesRequest')


result2 = client2.service.GetAccountBalances()
