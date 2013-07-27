# bfapi.py
# 17th July 2013

from betman import *
from betman.api import apiclient
import bfapimethod
import bfnonapimethod

# create suds clients
# read-only
clglob = apiclient.BFClient('global')
cluk = apiclient.BFClient('uk')
claus = apiclient.BFClient('aus')

# we have to login to betfair before we do anything
# this gives us a header with session token we use
# for all further requests
rhead = bfapimethod.BFLogin(clglob)
clglob.SetReqHead(rhead)
cluk.SetReqHead(rhead)
claus.SetReqHead(rhead)

# database interface
dbman = database.DBMaster()

# get all the root events
GetActiveEvents = bfapimethod.APIgetActiveEventTypes(clglob).call

# get markets will get markets for the selected top level ids
GetUKMarkets = bfapimethod.APIgetAllMarkets(cluk, dbman).call
GetAUSMarkets = bfapimethod.APIgetAllMarkets(claus, dbman).call

# selections and pricers for markets
GetSelections = bfnonapimethod.nonAPIgetSelections(cluk, dbman).call
#GetSelections = bfapimethod.APIgetMarket(cluk, dbman).call
#GetPricesCompressed = bfapimethod.APIgetMarketPricesCompressed(cluk, dbman).call
#GetPrices = bfapimethod.APIgetMarketPrices(cluk, dbman).call


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
