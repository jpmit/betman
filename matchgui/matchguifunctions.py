# matchguifunctions.py

from betman.api.bf import bfapi
from betman.api.bdaq import bdaqapi
import betman.matchmarkets.marketmatcher as marketmatcher
import betman.matchmarkets.matchconst as matchconst
from betman import database, const

# cache a list of matching markets for each event
MATCH_CACHE = {}

# cache the event list
BDAQ_EVENTS = []
BF_EVENTS = []

def _sort_match(item):
    """Sort matching markets by BDAQ start time"""
    return item[0].starttime

def match_markets(bdaqename):
    global BDAQ_EVENTS, BF_EVENTS, MATCH_CACHE
    
    # return cached info
    if bdaqename in MATCH_CACHE:
        return MATCH_CACHE[bdaqename]

    # get corresponding BF event name
    bfename = matchconst.EVENTMAP[bdaqename]

    if not BDAQ_EVENTS:
        # get top level events for BF and BDAQ
        BDAQ_EVENTS = bdaqapi.ListTopLevelEvents()
        # either don't try to login here or (better) modify betfair
        # library
        bfapi.Login()
        BF_EVENTS = bfapi.GetActiveEventTypes()
    
    # get markets for the selected event type
    bdaqmarkets = bdaqapi.\
                  GetEventSubTreeNoSelections([ev.id for ev in BDAQ_EVENTS
                                               if ev.name == bdaqename])
    bfmarkets = bfapi.GetAllMarketsUK([ev.id for ev in BF_EVENTS
                                       if ev.name == bfename])

    # get matching markets: note, for horse racing, this takes a long time
    # since it needs to call the BF API, which is heavily throttled.
    matchmarks = marketmatcher.get_match_markets(bdaqmarkets, bfmarkets)

    # get prices for all BDAQ markets, in order to get the total
    # matched, since this is not returned by the API call to get
    # markets.
    bdaqsels = bdaqapi.GetPrices([m[0].id for m in matchmarks])
    for (i, sels) in enumerate(bdaqsels):
        matchmarks[i][0].properties['totalmatched'] = sels[0].properties['totalmatched']

    # sort matching markets by starttime
    matchmarks.sort(key=_sort_match)

    MATCH_CACHE[bdaqename] = matchmarks

    return matchmarks
