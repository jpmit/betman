# bfapi.py
# James Mithen
# jamesmithen@gmail.com
#
# My internal API encapsulating the Betfair API.  This module should
# be imported by scripts that are requesting prices, making bets,
# etc..  Eventually, there should be two options, using the Betfair
# API in its entirety (a bad option due to the severe limitations on
# number of requests of the free BF API) or instead using my web
# scraping functionality.  The most sensible option, however, may well
# be to use some of the BF API and some of my own web scraping methods.

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
clglob = apiclient.BFClient('global')
cluk = apiclient.BFClient('uk')
claus = apiclient.BFClient('aus')

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
    
# selections and prices for markets
GetSelections = bfnonapimethod.nonAPIgetSelections(cluk, dbman).call

#GetSelections = bfapimethod.APIgetMarket(cluk, dbman).call
#GetPricesCompressed = bfapimethod.APIgetMarketPricesCompressed(cluk, dbman).call
#GetPrices = bfapimethod.APIgetMarketPrices(cluk, dbman).call

# below is for testing at the moment...
# remove this at some point
if __name__== '__main__':
    # get top level events
    events = GetActiveEvents()

    # lets limit to Motor Sport and Rugby Union for now
    elist =  ['Motor Sport','Rugby Union']
    events = [ev for ev in events if ev.name in elist]

    # get the market info for all of the markets we want
    ukmarkets = GetUKMarkets([ev.id for ev in events])
    ausmarkets = GetAUSMarkets([ev.id for ev in events])
    markets = ukmarkets + ausmarkets

    # get selections and prices for all markets
    # can use m.selections for a market object after this call

    # ANNOYING !!! need to call getselections below to get selection
    # names and ids (and called only once per 12 seconds max!!!)
    selections = GetSelections(109590806)
    # Then need to call one of the two functions below
    # can call getprices compressed 60 times p/m and getprices 10
    # times p/m (!!!!) this is for all markets....
    compressedoutput = GetPricesCompressed(109590806)
    output = GetPrices(109590806)
    selection = bfnonapimethod.GetSelections([109590806])
    dbman.close()
