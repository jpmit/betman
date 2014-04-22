# updaterfunctions.py
# James Mithen
# jamesmithen@gmail.com

"""
Functions for getting matching markets (using the APIs) and
matching selections (also using the APIs).
"""

import datetime
from operator import itemgetter
from betman.api.bf import bfapi
from betman.api.bdaq import bdaqapi
from betman.matching import marketmatcher, matchconst
from betman import const

# dict mapping event name to event id for each exchange, this is built
# the first time match_markets below is called.
_BDAQ_EVENTS = {}
_BF_EVENTS = {}

def _sort_match(item):
    """Key for sorting matching markets by BDAQ start time"""
    
    return item[0].starttime

def _display_order(bdaqmid):
    """
    Return list of selection id's in the order given by the BDAQ API
    (which is the display order on the website).
    """
    
    minfo = bdaqapi.GetMarketInformation([bdaqmid])
    # Note there can be some numbers missing in the display order!
    # E.g. we could have 5 selections, with display orders 1,2,3,4,6
    # respectively.  And, the display orders may not be in numerical
    # order, so we could also have e.g. 1,3,2,4,6.
    orderd = {}
    for m in minfo.Markets.Selections:
        orderd[m._DisplayOrder] = m._Id

    # from the dict, create a list with the sids.
    olist = [None]*max(orderd)
    for k in orderd:
        # k - 1 since zero indexing
        olist[k - 1] = orderd[k]

    # finally, remove all occurences of None from the list.
    flist = []
    for o in olist:
        if o is not None:
            flist.append(o)

    return flist

def get_ordered_selections(bdaqmid, bfmid):
    """
    Return bdaqsels, bfsels, lists of selection objects for BDAQ and
    BF respectively, ordered by bdaq display ordering.
    """

    # get prices from api: NB should check here that we actually got
    # selections.  If we didn't, bdaqsels[1] and bfsels[1] will be
    # non-empty (they will contain the single market id only).
    # Returned below is a dictionary of selections with keys that are
    # the sids.
    bdaqprices = bdaqapi.GetPrices_nApi([bdaqmid])
    bdaqsels = bdaqprices[0].values()[0]
    bfprices = bfapi.GetPrices_nApi([bfmid])
    print bfprices
    bfsels = bfprices[0].values()[0]

    # get lists of selections
    bdaqsellist = bdaqsels.values()
    bfsellist = bfsels.values()

    # get matching selections
    msels =  marketmatcher.get_match_selections([bdaqsellist],
                                                [bfsellist])

    # create dict with bdaq sid as key, bf sid as value
    mseldict = {k.id : v.id for (k, v) in msels}

    # get the BDAQ display order of selections
    dorder = _display_order(bdaqmid)

    # add display order to each BDAQ selection
    mlist = []
    for (i, d) in enumerate(dorder):
        # note d will not be in mseldict if we failed to match the
        # selection.
        if d in mseldict:
            mlist.append((d, mseldict[d]))
            bdaqsels[d].dorder = i

    # build and return ordered list of BDAQ selections
    bdaqorder = [bdaqsels[s[0]] for s in mlist]
    bforder = [bfsels[s[1]] for s in mlist]
    return bdaqorder, bforder

def get_matching_markets(bdaqename):
    """Get matching markets for a BetDaq event name."""

    global _BDAQ_EVENTS, _BF_EVENTS

    if not _BDAQ_EVENTS:
        # get top level events for BF and BDAQ
        bdaqevents = bdaqapi.ListTopLevelEvents()
        bfevents = bfapi.GetActiveEventTypes()
        _BDAQ_EVENTS = {e.name : e.id for e in bdaqevents}
        _BF_EVENTS = {e.name : e.id for e in bfevents}

    # check we were passed a valid event name
    if bdaqename not in _BDAQ_EVENTS:
        return []

    # get corresponding BF event name
    bfename = matchconst.EVENTMAP[bdaqename]
    
    # get all markets for the selected event type
    bdaqmarkets = bdaqapi.\
                  GetEventSubTreeNoSelections([_BDAQ_EVENTS[bdaqename]])
    bfmarkets = bfapi.GetAllMarketsUK([_BF_EVENTS[bfename]])

    # use matching engine to get matching markets
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

    # sort matching markets by starttime; NB could sort them by the
    # BDAQ official display order at some point if necessary.
    matchmarks.sort(key=_sort_match)

    return matchmarks
