# bfapiparse.py
# James Mithen
# jamesmithen@gmail.com

"""Functions for parsing the response that comes from the BF api."""

from betman import const, Market, Event, order, betlog
from betman.all.betexception import ApiError
import datetime

_EPS = 0.000001 # for fp arithmetic

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
        raise ApiError, service_ecode        

def ParsegetMUBets(res, odict):

    # here we override checking of errors, since the BF API returns an
    # error if no results are returned, but from our perspective there
    # is no problem with this, we just return an empty dict.
    if res.errorCode == 'NO_RESULTS':
        return {}

    _check_errors(res)

    #if len(res.bets.MUBet) != len(odict):
    #    betlog.betlog.debug('Got {0} results for updating {1} orders'\
    #                        .format(len(res.bets.MUBet), len(odict)))
    #    print res.bets.MUBet
    #    print odict
    #print res.bets.MUBet

    # The following is slightly complicated, this is because the BF
    # API can return multiple orders with the same betid, (although
    # they will have a different transactionId). We will get this if a
    # bet has been 'partially' matched.  From our perspective, this is
    # a single 'unmatched' bet.
    print 'odict from engine', odict
    print 'result', res

    # dictionary of orders we will return
    allorders = {}

    # first initialise each order as unmatched
    for oref in odict:
        o = odict[oref]
        idict = {'mid': o.mid, 'oref': oref, 'status' : order.UNMATCHED,
                 'matchedstake': 0.0, 'unmatchedstake': o.stake}
        allorders[oref] = order.Order(const.BFID, o.sid, o.stake,
                                      o.price, o.polarity, **idict)

    # go through each MUBet, and add the amount matched (if any) to
    # the appropriate order object.
    for r in res.bets.MUBet:

        if r.betStatus == 'M':

            # get the order in the order dict that has the matching id
            o = allorders[r.betId]
            
            # add matched amount
            o.matchedstake += r.size
            o.unmatchedstake -= r.size

    # go through all orders, and changed status of those with
    # matchedstake equal to original placed stake to order.MATCHED.
    for o in allorders.values():
        # fp arithmetic
        ms = o.matchedstake
        s = o.stake
        #print o, ms, s
        if (ms > s - _EPS) and (ms < s + _EPS):
            o.status = order.MATCHED

    return allorders

def ParseplaceBets(res, olist):

    # _check_errors only checks errors in the header and the footer,
    # we can have other errors that are returned in resultCode of each
    # (PlaceBetsResult) e.g resultCode = "INVALID_SIZE", and this even
    # if the main errorcode is "OK".  This is a 'known issue' in the
    # BF API, as detailed by the documentation
    # BetfairSportsExchangeAPIReferenceGuidev6.pdf, p114.
    print res
    _check_errors(res)
    tstamp = res.header.timestamp

#    print 'parse place bets:'
#    print olist
#    print res
    
    # check that we have one result for each order executed
    if len(res.betResults.PlaceBetsResult) != len(olist):
        raise ApiError, ('did not receive the correct number'
                         'of results from PlaceBets')

    allorders = {}
    # go through all results in turn and add to allorders list
    for betres, o in zip(res.betResults.PlaceBetsResult, olist):

        # first check that the bet was ok, there can be many possible
        # errors here, e.g. INVALID_SIZE: see
        # BetfairSportsExchangeAPIReferenceGuidev6.pdf, p119 for the
        # full list.
        if betres.resultCode != "OK":
            # we don't want to raise an exception here since the other
            # orders could have gone through ok, so print a warning
            # and skip to next order order id.
            betlog.betlog.debug('Warning: order {0} returned result {1}'\
                                .format(o, betres.resultCode))

        oref = betres.betId
        # check if we were matched
        matched = betres.sizeMatched
        if matched == o.stake:
            status = order.MATCHED
        else:
            # TODO: should we also have a part matched type? Probably.
            status = order.UNMATCHED

        odict = {'mid': o.mid, 'oref': oref, 'status': status,
                 'matchedstake': matched, 'unmatchedstake':
                 o.stake - matched, 'tplaced' : tstamp, 
                 'tupdated': tstamp}
        allorders[oref] = order.Order(const.BFID, o.sid, o.stake,
                                      o.price, o.polarity, **odict)
    
    return allorders

def ParsecancelBets(res, olist):
    """Return dict with key order id, value cancelled stake."""

    _check_errors(res)
    tstamp = res.header.timestamp

    # we should get information back for every order we tried to
    # cancel.
    odict = {o.oref: o for o in olist}
    
    # the API gives us a few things back that we are not using:
    # resultCode (which can be many things), sizeMatched, and success.
    # However, for our purposes, we should be able to figure
    # everything out from sizeCancelled.  This also means we maintain
    # consistency with the BDAQ API (for which sizeCancelled is the
    # only thing we can get).
    if isinstance(res.betResults.CancelBetsResult, list):
        data = res.betResults.CancelBetsResult
    else:
        data = [res.betResults.CancelBetsResult]
    for o in data:
        myo = odict[o.betId]
        myo.status = order.CANCELLED
        myo.tupdated = tstamp
        # store sizeMatched and sizeCancelled for now
        myo.sizeCancelled = o.sizeCancelled
        myo.sizeMatched = o.sizeMatched
    return odict

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
                              starttime, matched, **{'data': mdata}))

    return markets
