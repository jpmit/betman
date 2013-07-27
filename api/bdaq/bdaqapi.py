# app.py
# 24th June 2013

import bdaqapimethod
from betman import database
from betman.api import apiclient

# create suds clients
# read-only
rcl = apiclient.BDAQClient('readonly')
scl = apiclient.BDAQClient('secure')

# database interface
dbman = database.DBMaster()#create=True)

# get all the root events
GetTopLevelEvents = bdaqapimethod.APIListTopLevelEvents(rcl).call
# get markets will get 'subtree' and parse it for markets
GetMarkets = bdaqapimethod.APIGetEventSubTreeNoSelections(rcl, dbman).call
# selections and pricers for markets
GetSelections = bdaqapimethod.APIGetPrices(rcl, dbman).call

# top level events
events = GetTopLevelEvents()

# lets limit to Rugby Union, Formula 1 and Soccer for now
elist =  ['Soccer']#'Formula 1','Rugby Union', 'Soccer']
events = [ev for ev in events if ev.name in elist]

# get the subtree for all events we want
markets = GetMarkets([ev.id for ev in events], False)

# get selections and prices for all markets
# can use m.selections for a market object after this call
selections = GetSelections([m.id for m in markets])

dbman.close()
