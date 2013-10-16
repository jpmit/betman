# bfapiparse.py
# James Mithen
# jamesmithen@gmail.com

"""Functions for parsing the response that comes from the BF api."""

from betman import const, Market, Event, order
from betman.all.betexception import APIError

def ParsegetMUBets(res, odict):

    ecode = res.header.errorCode
    tstamp = res.header.timestamp
    
    if ecode != 'OK':
        raise APIError, 'getMUBets error, errorcode {0}'.format(ecode)

    if res.errorCode == 'NO_RESULTS':
        return {}

    # note we could get back more items than orders here, since an order
    # may have been partially matched to 2 or more others.
    if len(res.bets.MUBet) != len(odict):
        betlog.betlog.debug('Got {0} results for updating {1} orders'\
                            .format(len(res.bets.MUBet), len(odict)))
        print res.bets.MUBet
        print odict

    allorders = {}
    for r in res.bets.MUBet:

        # get the order id
        oref = r.betId

        # get the order in the order dict that has the matching id
        o = odict[oref]

        # note: will have to change this at some point for partial
        # matches
        if r.betStatus == 'U':
            status = order.UNMATCHED
            matched = 0.0
            unmatched = o.stake
        elif r.betStatus == 'M':
            status = order.MATCHED
            matched = o.stake
            unmatched = 0.0
        else:
            raise APIError, 'Received unknown order status {0}'.\
                  format(r.betStatus)
        
        oinfo = {'mid': o.mid, 'oref': oref, 'status': status,
                 'matchedstake' : matched, 'unmatchedstake' :
                 unmatched}

        allorders[oref] = order.Order(const.BFID, o.sid, o.stake,
                                      o.price, o.polarity, **oinfo)

    return allorders

def ParseplaceBets(res, olist):

    ecode = res.header.errorCode
    tstamp = res.header.timestamp
    
    if ecode != 'OK':
        raise APIError, 'placeBets error, errorcode {0}'.format(ecode)

    if const.DEBUG:
        print res

    # check that we have one result for each order executed
    assert len(res.betResults.PlaceBetsResult) == len(olist)

    allorders = {}
    # go through all results in turn and add to allorders list
    for betres, o in zip(res.betResults.PlaceBetsResult, olist):
        # order id
        oref = betres.betId
        # check if we were matched
        matched = betres.sizeMatched
        if matched == o.stake:
            status = order.MATCHED
        else:
            status = order.UNMATCHED

        odict = {'mid': o.mid, 'oref': oref, 'status': status,
                 'matchedstake': matched, 'unmatchedstake':
                 o.stake - matched}
        allorders[oref] = order.Order(const.BFID, o.sid, o.stake,
                                      o.price, o.polarity, **odict)
    
    return allorders

def ParsegetActiveEventTypes(res):
    events = []
    for e in res.eventTypeItems.EventType:
        events.append(Event(e.name, e.id, const.BFID))
    return events

def ParsegetAllMarkets(res):
    markets = []

    # check if there is some marketdata,
    if res.marketData is None:
        raise APIError, ('no market data returned, BF minorErrorCode'
                         ' {0}'.format(res.minorErrorCode))
        
    for mdata in res.marketData.split(':')[1:]:
        fields = mdata.split('~')
        # we will need to remove this erroneous Group D rubbish
        # at some point (!)        
        # fields are (in order, see also BF documentation):
        # [0] Market ID 
        # [1] Market name
        # [2] Market Type
        # [3] Market Status
        # [4] Event Date
        # [5] Menu Path
        # [6] Event Hierarchy (ids)
        # [7] Bet Delay
        # [8] Exchange Id (1 for UK/Worldwide, 2 for AUS)
        # [9] ISO3 Country code
        # [10] Last Refresh - time since cached data refreshed
        # [11] Number of Runners
        # [12] Number of Winners
        # [13] Total Amount Matched
        # [14] BSP Market
        # [15] Turning in Play

        # the full name of the market
        name = fields[5].replace('\\','|') + '|' + fields[1]
        myid = int(fields[0])
        # note parent id is the root one, we are skipping any
        # intermediate event ids
        pid = int(fields[6].split('/')[1])
        # are we inrunning?
        if fields[3] == 'ACTIVE':
            inrun = True
        else:
            inrun = False
        markets.append(Market(name, myid, pid, inrun, None, const.BFID))

    return markets
