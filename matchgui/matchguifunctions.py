# matchguifunctions.py

from betman.api.bf import bfapi
from betman.api.bdaq import bdaqapi
import betman.matchmarkets.marketmatcher as marketmatcher
import betman.matchmarkets.matchconst as matchconst
from betman import database, const

class GuiError(Exception):
    pass

# cache a list of matching markets for each event
MATCH_CACHE = {}

# matching selections keys are bdaq mid, values are [(bdaq_sid1,
# bf_sid1), ...] where bdaq_sid1 and bf_sid1 are matching selection
# ids.  Note the order is the same as displayed on the BDAQ website.
MATCHING_SELECTIONS_CACHE = {}

# cache the event list
BDAQ_EVENTS = []
BF_EVENTS = []

def _sort_match(item):
    """Sort matching markets by BDAQ start time"""
    
    return item[0].starttime

def market_name(bdaqename, index):
    """Return market name (of BDAQ rather than BF market."""

    global MATCH_CACHE
    return MATCH_CACHE[bdaqename][index][0].name

def display_order(bdaqmid):
    minfo = bdaqapi.GetMarketInformation([bdaqmid])
    order = [None]*len(minfo.Markets.Selections)
    for m in minfo.Markets.Selections:
        order[m._DisplayOrder - 1] = m._Id
    return order

def market_prices(bdaqename, index):
    """
    Return bdaqsels, bfsels, lists of selection objects for BDAQ and
    BF respectively.
    """
    
    global MATCH_CACHE, MATCHING_SELECTIONS_CACHE

    # get bdaq and bf market
    bdaqmark, bfmark = MATCH_CACHE[bdaqename][index]

    # get prices from api: NB should check here that we actually got
    # selections.  If we didn't, bdaqsels[1] and bfsels[1] will be
    # non-empty (they will contain the single market id only).
    # Returned below is a dictionary of selections with keys that are
    # the sids.
    bdaqsels = bdaqapi.GetPrices_nApi([bdaqmark.id])[0].values()[0]
    bfsels = bfapi.GetPrices_nApi([bfmark.id])[0].values()[0]
    
    if bdaqmark.id not in MATCHING_SELECTIONS_CACHE:

        # get lists of selections
        bdaqsellist = bdaqsels.values()
        bfsellist = bfsels.values()
            
        # get matching selections
        msels =  marketmatcher.get_match_selections([bdaqsellist],
                                                    [bfsellist])

        # create dict with bdaq sid as key, bf sid as value
        mseldict = {k.id : v.id for (k, v) in msels}

        # get the BDAQ display order of selections
        dorder = display_order(bdaqmark.id)

        # add sorting info to the cache
        mlist = []
        for d in dorder:
            # note d will not be in mseldict if we failed to match the
            # selection!
            if d in mseldict:
                mlist.append((d, mseldict[d]))
        # create cache entry
        MATCHING_SELECTIONS_CACHE[bdaqmark.id] = mlist

    # get selection ordering from cache
    osids = MATCHING_SELECTIONS_CACHE[bdaqmark.id]    

    bdaqorder = [bdaqsels[s[0]] for s in osids]
    bforder = [bfsels[s[1]] for s in osids]
    return bdaqorder, bforder

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
        matchmarks[i][0].properties['totalmatched'] = sels[0].\
                                                      properties['totalmatched']

    # sort matching markets by starttime; NB could sort them by the
    # BDAQ official display order at some point if necessary.
    matchmarks.sort(key=_sort_match)

    MATCH_CACHE[bdaqename] = matchmarks

    return matchmarks
