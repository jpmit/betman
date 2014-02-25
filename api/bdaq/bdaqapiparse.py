# bdaqapiparse.py
# James Mithen
# jamesmithen@gmail.com

"""
Functions for parsing the data received from BDAQ Api calls.  The SUDS
library has done most of the work for us here, we just need to extract
the data we want.
"""

from betman import const, util, Market, Selection, Event, order
from betman.all import const
from betman.all.betexception import ApiError

def _check_errors(resp):
    """
    Check errors from BDAQ API response.  This function is called in
    all of the parsing functions below before extracting any data from
    the response.
    """

    retcode = resp.ReturnStatus._Code

    if retcode != 0:
        print resp
        raise ApiError, '{0} {1}'.format(retcode,
                                         resp.ReturnStatus._Description)

def ParseListTopLevelEvents(resp):

    _check_errors(resp)
    
    events = []
    for ec in resp.EventClassifiers:
        events.append(Event(ec._Name, ec._Id, **dict(ec)))
    return events

def ParseGetEventSubTreeNoSelections(resp):

    _check_errors(resp)
    
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
        _ParseEventClassifier(evclass,'', markets)
        allmarkets = allmarkets + markets
        
    # hack: currently markets are duplicated multiple times (is this
    # an API error?); we want only unique markets here
    umarkets = util.unique(allmarkets)
    return umarkets

def _ParseEventClassifier(eclass, name='', markets=[]):
    """
    Get Markets from a Top Level Event, e.g. 'Rugby Union'.
    Note that we skip a level here, e.g. We would go Rugby ->
    Lions Tour -> market, but here we will just find all rugby
    union markets, regardless of their direct ancester.
    """

    name = name + '|' + eclass._Name
    pid = eclass._ParentId
    myid = eclass._Id

    if hasattr(eclass, 'EventClassifiers'):
        for e in eclass.EventClassifiers:
            _ParseEventClassifier(e, name, markets)
    else:
        if hasattr(eclass, 'Markets'):
            for mtype in eclass.Markets:
                markets.append(Market(const.BDAQID,
                                      name + '|' + mtype._Name,
                                      mtype._Id,
                                      pid,
                                      mtype._IsCurrentlyInRunning,
                                      mtype._StartTime,
                                      **dict(mtype)))

def ParseGetPrices(marketids, resp):

    _check_errors(resp)

    # if we only called with a single market id, we won't have a list
    if len(marketids) == 1:
        resp.MarketPrices = [resp.MarketPrices]
        
    # check market prices is right length
    assert len(resp.MarketPrices) == len(marketids)

    allselections = []
    for (mid, mprice) in zip(marketids, resp.MarketPrices):
        
        # there are a few things about the market returned before the
        # selection types.  The main thing we want is the total
        # matched amount on the market, since this is not available
        # via the getmarkets call (unlike for BF).

        if hasattr(mprice, '_TotalMatchedAmount'):
            # TODO: figure out why not every market price has this
            # attribute.
            total_matched = mprice._TotalMatchedAmount
        else:
            total_matched = 0.0
        
        # list of selections for this marketid
        allselections.append([])

        # go through each selection for the market.  For some reason
        # the Api is returning every selection twice, although this
        # could be an error with the SOAP library (?).

        # are there any selections?
        if not hasattr(mprice,'Selections'):
            # can reach here if market suspended, in this case
            # mprice._ReturnCode = 16, corresponding to 'market
            # neither suspended nor active'.
            continue

        nsel = len(mprice.Selections)

        # we store the market withdrawal sequence number in every
        # selection instance, since this is needed to place a bet on
        # the selection.  This is mainly important for horse racing
        # markets, for which there are often withdrawals before the
        # race (i.e. horses that do not run), which in turn makes this
        # sequence number non-zero.  For other markets, the sequence
        # number is usually zero.
        wsn = mprice._WithdrawalSequenceNumber

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
            # store all the selection information and the total
            # matched amount from the header
            kwdict = dict(sel)
            kwdict['totalmatched'] = total_matched
            
            # Note the only data directly concerning the selection
            # that we are not storing in the selection instance is the
            # 'deduction factor'.
            allselections[-1].append(Selection(const.BDAQID, sel._Name, sel._Id,
                                               mid,
                                               sel._MatchedSelectionForStake,
                                               sel._MatchedSelectionAgainstStake,
                                               lastmatchoccur,
                                               lastmatchprice,
                                               lastmatchamount,
                                               bprices, lprices,
                                               sel._ResetCount, wsn,
                                               **kwdict))
    return allselections

def ParseListBootstrapOrders(resp):
    """
    Parse a single order, return order object.  Note there are a few
    things the Api is returning that we are ignoring here.
    """

    _check_errors(resp)

    # no orders returned; end of bootstrapping process.
    if not hasattr(resp, 'Orders'):
        return {}

    # create and return list of order objects.    
    allorders = {}
    for o in resp.Orders.Order:
        sid = o._SelectionId
        ustake = o._UnmatchedStake
        mstake = o._MatchedStake
        stake = ustake + mstake
        # note we also get back '_MatchedPrice' if matched; this could
        # be better than '_RequestedPrice'.
        price = o._RequestedPrice
        pol = o._Polarity
        oref = o._Id
        status = o._Status
        
        allorders[oref] = order.Order(const.BDAQID, sid, stake, price,
                                      pol, **{'oref': oref,
                                              'status': status,
                                              'matchedstake': mstake,
                                              'unmatchedstake': ustake})

    return allorders

def ParsePlaceOrdersNoReceipt(resp, olist):
    """Return list of order objects."""

    _check_errors(resp)
    tstamp = resp.Timestamp

    # list of order refs - I am presuming BDAQ returns them in the order
    # the orders were given!
    orefs = resp.OrderHandles.OrderHandle

    # create and return order object.  Note we set status to UNMATCHED,
    # and unmatched stake and matched stake accordingly.
    allorders = {}
    for (o, ref) in zip(olist, orefs):
        allorders[ref] = order.Order(const.BDAQID, o.sid, o.stake, o.price,
                                     o.polarity, **{'oref': ref, 'mid': o.mid,
                                                    'status': order.UNMATCHED,
                                                    'matchedstake': 0.0,
                                                    'unmatchedstake': o.stake,
                                                    # we will write t placed to the DB
                                                    'tplaced': tstamp,
                                                    'tupdated': tstamp})
    return allorders

def ParseUpdateOrdersNoReceipt(resp, olist):
    """Return dictionary of updated order objects"""

    _check_errors(resp)
    tstamp = resp.Timestamp

    # the dict of orders we wanted to update
    odict = {o.oref : o for o in olist}

    if hasattr(resp, 'Orders'):
        if isinstance(resp.Orders.Order, list):
            data = resp.Orders.Order
        else:
            data = [resp.Orders.Order]
        for o in data:
            retcode = o._ReturnCode
            if (retcode == 0):
                # we just need to update the stake by adding
                # deltastake, the price is already the new price.
                myo = odict[o._BetId]
                myo.stake += myo.deltastake
                # delete attribute since don't want to confuse
                # ourselves later.
                del myo.deltastake
            elif (retcode == 22 or retcode == 306):
                # the above return codes seem harmless, all others
                # will raise ApiError (see below for what all of the
                # return codes, including those above, mean).
                pass
            else:
                # there are quite a few possible return codes here
                # (from BDAQ API docs):
                # RC015	MarketNotActive
                # RC017	SelectionNotActive
                # RC021	OrderDoesNotExist
                # RC022	NoUnmatchedAmount
                # RC114	ResetHasOccurred
                # RC128	TradingCurrentlySuspended
                # RC131	InvalidOdds
                # RC136	WithdrawalSequenceNumberIsInvalid
                # RC137	MaximumInputRecordsExceeded
                # RC208	PunterSuspended
                # RC240	PunterProhibitedFromPlacingOrders
                # RC241	InsufficientPunterFunds
                # RC271	OrderAPIInProgress 
                # RC274	PunterOrderMismatch
                # RC293	InRunningDelayInEffect
                # RC299	DuplicateOrderSpecified
                # RC302	PunterIsSuspendedFromTrading 
                # RC305	ExpiryTimeInThePast
                # RC306	NoChangeSpecified
                # RC406	PunterIsBlacklisted
                raise ApiError, ('could not update order {0}'
                                 ', return code {1}'.\
                                 format(o._BetId, o._ReturnCode))

    return odict

def ParseCancelOrders(resp, olist):
    """Return dict of order objects."""

    _check_errors(resp)
    tstamp = resp.Timestamp

    print resp

    # warning: according the the BDAQ API docs, we won't get
    # information back about any order that is subject to an in
    # running delay.

    odict = {o.oref: o for o in olist}

    orefseen = []
    for o in resp.Orders.Order:
        oref = o._OrderHandle
        orefseen.append(oref)

        myo = odict[oref]
        myo.status = order.CANCELLED
        myo.tupdated = tstamp

    # return information on the order refs we saw (which may not be
    # all of them, due to the in running delay mentioned above).
    return {k: odict[k] for k in odict if k in orefseen}

def ParseCancelAllOrdersOnMarket(resp):
    """Return dict with key order id, value cancelled stake """

    _check_errors(resp)
    tstamp = resp.Timestamp

    ocancel = {}
    # need hasattr since we get success even when no orders cancelled
    if hasattr(resp, 'Order'):
        if isinstance(resp.Order, list):
            data = resp.Order
        else:
            data = [resp.Order]
        for o in data:
            ocancel[o._OrderHandle] = o._cancelledForSideStake
    return ocancel

def ParseCancelAllOrders(resp):
    """Return dict with key order id, value cancelled stake """

    _check_errors(resp)
    tstamp = resp.Timestamp

    ocancel = {}
    # this is very similar to the above, but there is an extra layer
    # of 'nesting' in the response (for some unfathomable reason).
    if hasattr(resp, 'Orders'):
        if isinstance(resp.Orders.Order, list):
            data = resp.Orders.Order
        else:
            data = [resp.Orders.Order]
        for o in data:
            ocancel[o._OrderHandle] = o._cancelledForSideStake
    return ocancel

def ParseGetAccountBalances(resp):
    """
    Returns account balance information by parsing output from BDAQ
    Api function GetAccountBalances.
    """

    _check_errors(resp)

    return {'available': resp._AvailableFunds,
            'balance': resp._Balance,
            'credit': resp._Credit,
            'exposure': resp._Exposure}

def ParseListOrdersChangedSince(resp):
    """Returns list of orders that have changed"""

    _check_errors(resp)
    tstamp = resp.Timestamp
    
    if not hasattr(resp, 'Orders'):
        # no orders have changed
        return {}

    # store the sequence numbers of the orders: we need to return the
    # maximum sequence number so that the next time we call the API
    # function we won't return this again!
    seqnums = []

    allorders = {}
    for o in resp.Orders.Order:

        # From API docs, order _Status can be
        # 1 - Unmatched.  Order has SOME amount available for matching.
        # 2 - Matched (but not settled).
        # 3 - Cancelled (at least some part of the order was unmatched).
        # 4 - Settled.
        # 5 - Void.
        # 6 - Suspended.  At least some part unmatched but is suspended.

        # Note: at the moment we are not storing all of the data that
        # comes from the BDAQ API function, only the information that
        # seems useful...
        odict = {'oref': o._Id,
                 'status': o._Status,
                 'matchedstake' : o._MatchedStake,
                 'unmatchedstake': o._UnmatchedStake,
                 'tupdated': tstamp}

        allorders[o._Id] = order.Order(const.BDAQID, o._SelectionId,
                                       o._MatchedStake + o._UnmatchedStake,
                                       o._RequestedPrice, o._Polarity,
                                       **odict)
        # store sequence number
        seqnums.append(o._SequenceNumber)

    return allorders, max(seqnums)
