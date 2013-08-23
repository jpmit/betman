# bdaqapi.py
# James Mithen
# jamesmithen@gmail.com

import bdaqapimethod
from betman import database
from betman.api import apiclient

# any constants that we might need to modify

# time in seconds to sleep between calling APIGetPrices (when called
# with > 50 market ids).
PRICETHROTTLE = 3

# create suds clients
# There is only 1 WSDL file, but this has two 'services'.  The 
# services are for 'readonly' methods and 'secure' methods. Secure
# methods use an https:// url and send the 
# read-only
rcl = apiclient.BDAQClient('readonly')
scl = apiclient.BDAQClient('secure')

# database interface
dbman = database.DBMaster()

# get all the root events
GetTopLevelEvents = bdaqapimethod.APIListTopLevelEvents(rcl).call
# get markets will get 'subtree' and parse it for markets
GetMarkets = bdaqapimethod.APIGetEventSubTreeNoSelections(rcl, dbman).call
# selections and pricers for markets
GetSelections = bdaqapimethod.APIGetPrices(rcl, dbman, PRICETHROTTLE).call

GetMarketInformation = bdaqapimethod.APIGetMarketInformation(rcl, dbman).call

# make order
PlaceOrder = bdaqapimethod.APIPlaceOrdersNoReceipt(scl, dbman).call
