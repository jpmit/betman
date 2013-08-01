from betman import Market, Selection, Event

def ParseEvents(resp):
    events = []
    for ec in resp.EventClassifiers:
        events.append(Event(ec._Name, ec._Id, 1))
    return events

def ParsePrices(marketids, resp):
    retcode = resp.ReturnStatus._Code
    tstamp = resp.Timestamp

    # check the Return Status is zero (success)
    # and not:
    # 8 - market does not exist
    # 16 - market neither suspended nor active
    # 137 - maximuminputrecordsexceeded (should never get this)
    # 406 - punter blacklisted
    if retcode == 406:
        raise APIError, 'punter is blacklisted'

    # check market prices is right length
    print len(resp.MarketPrices)
    print resp
    assert len(resp.MarketPrices) == len(marketids)

    allselections = []
    for (mid, mprice) in zip(marketids, resp.MarketPrices):
        # list of selections for this marketid
        allselections.append([])
        # go through each selection for the market
        # for some reason the API is returning every selection
        # twice, although this could be an error with the SOAP
        # library.

        # are there any selections?
        if not hasattr(mprice,'Selections'):
            # can reach here if market suspended
            break
        # double listing problem
        nsel = len(mprice.Selections) / 2

        for sel in mprice.Selections[:nsel]:
            # lists of back and lay prices
            # note the response object may not have these attributes
            # if no odds are on offer
            if hasattr(sel, 'ForSidePrices'):
                # if we only have one price on offer
                # there is no array
                if (isinstance(sel.ForSidePrices,list)):
                    bprices = [(p._Price, p._Stake) for p in
                               sel.ForSidePrices]                    
                else:
                    bprices = [(sel.ForSidePrices._Price,
                                sel.ForSidePrices._Stake)]                    
            else:
                bprices = []
            if hasattr(sel, 'AgainstSidePrices'):
                # if we only have one price on offer
                # there is no array
                if (isinstance(sel.AgainstSidePrices,list)):
                    lprices = [(p._Price, p._Stake) for p in
                               sel.AgainstSidePrices]                    
                else:
                    # only one price
                    lprices = [(sel.AgainstSidePrices._Price,
                                sel.AgainstSidePrices._Stake)]
            else:
                lprices = []
            # create selection object using given data
            # we need to handle the case of no matches yet, since in
            # this case the response is missing certain fields.
            if not (sel._MatchedSelectionForStake or
                    sel._MatchedSelectionAgainstStake):
                lastmatchoccur = None
                lastmatchprice = None
                lastmatchamount = None
            else:
                lastmatchoccur = sel._LastMatchedOccurredAt
                lastmatchprice = sel._LastMatchedPrice
                lastmatchamount = sel._LastMatchedForSideAmount
            allselections[-1].append(Selection(sel._Name, sel._Id, mid,
                                               sel._MatchedSelectionForStake,
                                               sel._MatchedSelectionAgainstStake,
                                               lastmatchoccur,
                                               lastmatchprice,
                                               lastmatchamount,
                                               bprices, lprices))
    return allselections

def ParseEventSubTree(resp):
    # first thing is return status
    # return code below should be zero if successful
    retcode = resp.ReturnStatus._Code
    tstamp = resp.Timestamp    
    # check the Return Status is zero (success)
    # and not:
    # 5 - event classifier does not exist
    # 137 - maximuminputrecordsexceeded
    # 406 - punter blacklisted
    if retcode == 406:
        raise APIError, 'punter is blacklisted'
    
    allmarkets = []
    markets = []
    # go through each event class in turn, an event class is
    # e.g. 'Rugby Union','Formula 1', etc.
    # slight trick here:
    # if we only polled a single event class, then resp[2] is
    # not a list, so we need to convert it to a list
    if isinstance(resp[2], list):
        data = resp[2]
    else:
        data = [resp[2]]
    for evclass in data:
        ParseEventClassifier(evclass,'', markets)
        allmarkets = allmarkets + markets
    return allmarkets

def ParseEventClassifier(eclass, name='', markets=[]):
    """Get Markets from a Top Level Event, e.g. 'Rugby Union'.
    Note that we skip a level here, e.g. We would go Rugby ->
    Lions Tour -> market, but here we will just find all rugby
    union markets, regardless of their direct ancester."""

    name = name + '|' + eclass._Name
    pid = eclass._ParentId
    myid = eclass._Id

    if hasattr(eclass, 'EventClassifiers'):
        for e in eclass.EventClassifiers:
            ParseEventClassifier(e, name, markets)
    else:
        if hasattr(eclass, 'Markets'):
            for mtype in eclass.Markets:
                markets.append(Market(name + '|' + mtype._Name,
                                      mtype._Id,
                                      pid,
                                      mtype._IsCurrentlyInRunning))
