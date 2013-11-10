# bdaqapi.py
# James Mithen
# jamesmithen@gmail.com

"""The BetDaq Api functions."""

import bdaqapimethod
import bdaqnonapimethod
from betman import database
from betman.api import apiclient

# time in seconds to sleep between calling ApiGetPrices (when called
# with > 50 market ids).
_PRICETHROTTLE = 10

# create suds clients.  There is only 1 WSDL file, but this has two
# 'services'.  The services are for 'readonly' methods and 'secure'
# methods. Secure methods use an https:// url and require the user's
# Betdaq username and password in the SOAP headers, read-only methods
# use http:// and only require username.
_rcl = apiclient.BDAQApiClient('readonly')
_scl = apiclient.BDAQApiClient('secure')
_ncl = apiclient.BDAQNonApiClient()

def set_user(name, password):
    """
    Set username and password for SOAP headers.  Note that these are
    automatically set to be const.BDAQUSER and const.BDAQPASS,
    respectively, so we only need to call this method if we don't have
    these values set.
    """
    
    _rcl.set_headers(name, password)
    _scl.set_headers(name, password)

# database interface
_dbman = database.DBMaster()

# the Api functions appear below, first 'readonly' methods, then
# 'secure' methods, in the order that these appear in the Betdaq Api
# docs (but note that not all of the Api methods are implemented
# here).

# get all the root events
ListTopLevelEvents = bdaqapimethod.ApiListTopLevelEvents(_rcl).call

# get 'subtree' and parse it for markets
GetEventSubTreeNoSelections = bdaqapimethod.\
                              ApiGetEventSubTreeNoSelections(_rcl, _dbman).call

# get information for some market ids, e.g. starttime etc.
GetMarketInformation = bdaqapimethod.\
                       ApiGetMarketInformation(_rcl, _dbman).call

# get prices for some market ids
GetPrices = bdaqapimethod.\
            ApiGetPrices(_rcl, _PRICETHROTTLE).call

# get account information
GetAccountBalances = bdaqapimethod.\
                     ApiGetAccountBalances(_scl, _dbman).call

# update order status
ListOrdersChangedSince = bdaqapimethod.\
                         ApiListOrdersChangedSince(_scl, _dbman).call

# call ListBootstrapOrders repeatedly at startup
ListBootstrapOrders = bdaqapimethod.\
                      ApiListBootstrapOrders(_scl, _dbman).call

# make order(s)
PlaceOrdersNoReceipt = bdaqapimethod.\
                       ApiPlaceOrdersNoReceipt(_scl, _dbman).call

# cancel orders
CancelOrders = bdaqapimethod.ApiCancelOrders(_scl, _dbman).call

# which Api services (hopefully none) am I currently blacklisted from?
ListBlacklistInformation = bdaqapimethod.\
                           ApiListBlacklistInformation(_scl).call

# non Api (screen scraping) functions appear below.  These are
# suffixed with _nApi.

# get prices for some market ids
GetPrices_nApi = bdaqnonapimethod.NonApiGetPrices(_ncl, _dbman).call
