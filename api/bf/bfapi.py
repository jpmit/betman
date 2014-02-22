# bfapi.py
# James Mithen
# jamesmithen@gmail.com

"""
My internal Api encapsulating the Betfair Api.  This module should
be imported by scripts that are requesting prices, making bets,
etc..  Eventually, there should be two options, using the Betfair
Api in its entirety (a bad option due to the severe limitations on
number of requests of the free BF Api) or instead using my web
scraping functionality.  The most sensible option, however, may well
be to use some of the BF Api and some of my own web scraping
methods.
"""

from betman import *
from betman.api import apiclient
import bfapimethod
import bfnonapimethod

# create suds clients
# There are 3 WSDL files:
# * one 'global' (login, get account balances etc.)
# * one for the UK exchange, and
# * one for the Australian exchange
# each gets a different handling client here.
clglob = apiclient.BFApiClient('global')
cluk = apiclient.BFApiClient('uk')
claus = apiclient.BFApiClient('aus')
cluknonapi = apiclient.BFNonApiClient('uk')

# database interface (this will create DB if necessary)
dbman = database.DBMaster()

# we have to login to betfair before we do anything. This gives us a
# header with session token we use for all further BF Api calls (all
# of the other Api functions need this session token)
def Login():
    rhead = bfapimethod.BFLogin(clglob)
    clglob.set_reqheader(rhead)
    cluk.set_reqheader(rhead)
    claus.set_reqheader(rhead)

# get all the root events
GetActiveEventTypes = bfapimethod.ApigetActiveEventTypes(clglob).call

# get markets will get markets for the selected top level ids
GetAllMarketsUK = bfapimethod.ApigetAllMarkets(cluk, dbman).call
GetAllMarketsAUS = bfapimethod.ApigetAllMarkets(claus, dbman).call
    
# get static market information
GetMarket = bfapimethod.ApigetMarket(cluk, dbman).call

# get (additional(?)) market info
GetMarketInfo = bfapimethod.ApigetMarketInfo(cluk, dbman).call

#GetSelections = bfapimethod.ApigetMarket(cluk, dbman).call
#GetPricesCompressed = bfapimethod.ApigetMarketPricesCompressed(cluk, dbman).call
#GetPrices = bfapimethod.ApigetMarketPrices(cluk, dbman).call
PlaceBets = bfapimethod.ApiplaceBets(cluk, dbman).call

# cancel bets 
CancelBets = bfapimethod.ApicancelBets(cluk, dbman).call

# update bets
UpdateBets = bfapimethod.ApiupdateBets(cluk, dbman).call

# this only checks if matched or unmatched at the moment
GetBetStatus = bfapimethod.ApigetMUBets(cluk, dbman).call

# non Api (screen scraping) functions appear below.  These are suffixed with _nApi.

# get market information
GetMarket_nApi = bfnonapimethod.NonApigetMarket(cluknonapi, dbman).call

# get prices
GetPrices_nApi = bfnonapimethod.NonApigetPrices(cluknonapi,
                                                dbman).call
