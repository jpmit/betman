# bfapi.py
# James Mithen
# jamesmithen@gmail.com

"""
My internal API encapsulating the Betfair API.  This module should
be imported by scripts that are requesting prices, making bets,
etc..  Eventually, there should be two options, using the Betfair
API in its entirety (a bad option due to the severe limitations on
number of requests of the free BF API) or instead using my web
scraping functionality.  The most sensible option, however, may well
be to use some of the BF API and some of my own web scraping
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
clglob = apiclient.BFAPIClient('global')
cluk = apiclient.BFAPIClient('uk')
claus = apiclient.BFAPIClient('aus')
cluknonapi = apiclient.BFnonAPIClient('uk')

# database interface (this will create DB if necessary)
dbman = database.DBMaster()

# we have to login to betfair before we do anything. This gives us a
# header with session token we use for all further BF API calls (all
# of the other API functions need this session token)
def Login():
    rhead = bfapimethod.BFLogin(clglob)
    clglob.SetReqHead(rhead)
    cluk.SetReqHead(rhead)
    claus.SetReqHead(rhead)

# get all the root events
GetActiveEvents = bfapimethod.APIgetActiveEventTypes(clglob).call

# get markets will get markets for the selected top level ids
GetUKMarkets = bfapimethod.APIgetAllMarkets(cluk, dbman).call
GetAUSMarkets = bfapimethod.APIgetAllMarkets(claus, dbman).call
    
# selections and prices for markets - not using the API
GetSelections = bfnonapimethod.nonAPIgetSelections(cluknonapi,
                                                   dbman).call
GetMarket = bfapimethod.APIgetMarket(cluk, dbman).call
GetMarketInfo = bfapimethod.APIgetMarketInfo(cluk, dbman).call

#GetSelections = bfapimethod.APIgetMarket(cluk, dbman).call
#GetPricesCompressed = bfapimethod.APIgetMarketPricesCompressed(cluk, dbman).call
#GetPrices = bfapimethod.APIgetMarketPrices(cluk, dbman).call
PlaceBets = bfapimethod.APIplaceBets(cluk, dbman).call

# cancel bets doesn't seem to be working at the moment...
CancelBets = bfapimethod.APIcancelBets(cluk, dbman).call

# this only checks if matched or unmatched at the moment
GetBetStatus = bfapimethod.APIgetMUBets(cluk, dbman).call
