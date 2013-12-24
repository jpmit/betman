# bfapiparse.py
# James Mithen
# jamesmithen@gmail.com

"""Functions for parsing the response that comes from the BF api."""

from betman import const, Market, Event, order
from betman.all.betexception import ApiError
import datetime

def _check_errors(res):
    """
    Check errors from BF API response.  This function is called before
    extracting the data using the functions below.
    We check (i) Any API errors, which are contained in the header
             (ii) Any 'service specific' errors.
    """

    # first we check any overall API
    api_ecode = res.header.errorCode

    if api_ecode != 'OK':
        print res
        raise ApiError, api_ecode

    # next, we check any 'service specific errors'
    service_ecode = res.errorCode

    if service_ecode != 'OK':
        print res
        raise ApiError, api_ecode        

def ParsegetMUBets(res, odict):

    # here we override checking of errors, since the BF API returns an
    # error if no results are returned, but from our perspective there
    # is no problem with this, we just return an empty dict.
    if res.errorCode == 'NO_RESULTS':
        return {}

    _check_errors(res)

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
            raise ApiError, 'Received unknown order status {0}'.\
                  format(r.betStatus)
        
        oinfo = {'mid': o.mid, 'oref': oref, 'status': status,
                 'matchedstake' : matched, 'unmatchedstake' :
                 unmatched}

        allorders[oref] = order.Order(const.BFID, o.sid, o.stake,
                                      o.price, o.polarity, **oinfo)

    return allorders

def ParseplaceBets(res, olist):

    _check_errors(res)
    
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
        events.append(Event(e.name, e.id))
    return events

def ParsegetAllMarkets(res):

    _check_errors(res)
    markets = []
        
    for mdata in res.marketData.split(':')[1:]:
        fields = mdata.split('~')
        # we will need to remove this erroneous Group D rubbish
        # at some point (!)        
        # fields are (in order, see also BF documentation):
        # [0]  Market ID 
        # [1]  Market name
        # [2]  Market Type
        # [3]  Market Status
        # [4]  Event Date
        # [5]  Menu Path
        # [6]  Event Hierarchy (ids)
        # [7]  Bet Delay
        # [8]  Exchange Id (1 for UK/Worldwide, 2 for AUS)
        # [9]  ISO3 Country code
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
        
        # Note from BF docs market status can be
        # ACTIVE 	  Market is open and available for betting.
        # CLOSED 	  Market is finalised, bets to be settled.
        # INACTIVE  Market is not yet available for betting.
        # SUSPENDED Market is temporarily closed for betting, possibly
        #           due to pending action such as a goal scored during
        #           an in-play match or removing runners from a race.
        #
        # Here we use bet delay to determine whether market is in
        # running or not.
        delay = int(fields[7])
        if delay != 0:
            inrun = True
        else:
            inrun = False
            
        # market starttime, from seconds since 1970 GMT
        starttime = datetime.datetime.fromtimestamp(int(fields[4]) / 1000)
        # total matched in GBP
        matched = float(fields[13])
        
        # we pass the entire string from BF as the last argument here,
        # so that we can access all the data from the API if necessary
        # via properties['data'].
        markets.append(Market(const.BFID, name, myid, pid, inrun,
                              starttime, 
                              **{'data': mdata, 'totalmatched': matched}))

    return markets
