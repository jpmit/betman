# matchguifunctions.py
# James Mithen
# jamesmithen@gmail.com

"""
A lot of ugly stuff that goes on behind the scenes...
TODO: sort this out a bit.
"""

import datetime
from operator import itemgetter
from betman.api.bf import bfapi
from betman.api.bdaq import bdaqapi
import betman.matchmarkets.marketmatcher as marketmatcher
import betman.matchmarkets.matchconst as matchconst
from betman import database, const

class GuiError(Exception):
    pass

# cache the event list
BDAQ_EVENTS = []
BF_EVENTS = []

# interface for writing the the DB
_dbman = database.DBMaster()

def _sort_match(item):
    """Key for sorting matching markets by BDAQ start time"""
    
    return item[0].starttime

def display_order(bdaqmid):
    """
    Return list of selection id's in the order given by the BDAQ API
    (which is the display order on the website).
    """
    
    minfo = bdaqapi.GetMarketInformation([bdaqmid])
    order = [None]*len(minfo.Markets.Selections)
    for m in minfo.Markets.Selections:
        order[m._DisplayOrder - 1] = m._Id
    return order

def market_prices(bdaqmid, bfmid):
    """
    Return bdaqsels, bfsels, lists of selection objects for BDAQ and
    BF respectively, ordered by bdaq display ordering.
    """

    # get prices from api: NB should check here that we actually got
    # selections.  If we didn't, bdaqsels[1] and bfsels[1] will be
    # non-empty (they will contain the single market id only).
    # Returned below is a dictionary of selections with keys that are
    # the sids.
    bdaqsels = bdaqapi.GetPrices_nApi([bdaqmid])[0].values()[0]
    bfsels = bfapi.GetPrices_nApi([bfmid])[0].values()[0]

    # write selections to the DB
    # TODO: write convenience function somewhere so this is a single
    # line, and fix and document APIs so we know where we should be
    # saving this information.
    _dbman.WriteSelections(bdaqsels.values() + bfsels.values(),
                           datetime.datetime.now())    

    # get lists of selections
    bdaqsellist = bdaqsels.values()
    bfsellist = bfsels.values()

    # get matching selections
    msels =  marketmatcher.get_match_selections([bdaqsellist],
                                                [bfsellist])

    # create dict with bdaq sid as key, bf sid as value
    mseldict = {k.id : v.id for (k, v) in msels}

    # get the BDAQ display order of selections
    dorder = display_order(bdaqmid)

    # add sorting info to the cache
    mlist = []
    tnow = datetime.datetime.now()
    for (i, d) in enumerate(dorder):
        # note d will not be in mseldict if we failed to match the
        # selection!
        if d in mseldict:
            mlist.append((d, mseldict[d]))
            bdaqsels[d].dorder = i
            # update the selection in the database so that we have
            # the display order stored for next time we start-up.
            _dbman.WriteSelections([bdaqsels[d]], tnow)

    bdaqorder = [bdaqsels[s[0]] for s in mlist]
    bforder = [bfsels[s[1]] for s in mlist]
    return bdaqorder, bforder

def match_markets(bdaqename):
    global BDAQ_EVENTS, BF_EVENTS

    # get corresponding BF event name
    bfename = matchconst.EVENTMAP[bdaqename]

    if not BDAQ_EVENTS:
        # get top level events for BF and BDAQ
        BDAQ_EVENTS = bdaqapi.ListTopLevelEvents()
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

    # remove any markets for which we didn't get any bdaq sels
    rem = [i for i in range(len(bdaqsels)) if not bdaqsels[i]]
    print 'removing markets', rem
    rem.reverse()
    for i in rem:
        matchmarks.pop(i)
        bdaqsels.pop(i)

    for (i, sels) in enumerate(bdaqsels):
        if sels:
            matchmarks[i][0].totalmatched = sels[0].\
                                            properties['totalmatched']

    # Write market stuff to the DB
    # (i) write details of the matching markets
    _dbman.WriteMarketMatches(matchmarks)
    # (ii) update the bdaqmarkets, since now have totalmatched
    bdmarks = [itemgetter(0)(i) for i in matchmarks]
    _dbman.WriteMarkets(bdmarks, datetime.datetime.now())
        
    # sort matching markets by starttime; NB could sort them by the
    # BDAQ official display order at some point if necessary.
    matchmarks.sort(key=_sort_match)

    return matchmarks
