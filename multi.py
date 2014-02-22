# multi.py
# James Mithen
# jamesmithen@gmail.com

"""Any multithreaded methods."""

from betman import const, betexception
from betman.api.bf import bfapi
from betman.api.bdaq import bdaqapi
from threading import Thread, active_count
from Queue import Queue
from urllib2 import URLError

def update_prices(middict):
    """
    Get new prices.  Here middict is a dictionary with keys
    const.BDAQID, const.BFID, and items which are the market ids.
    Return two dictionaries, first contains market information, second
    contains any erroneous mids, which may be e.g. those markets that
    have now finished.
    """

    q = Queue()
    prices = {} # the prices
    emids = {}  # the market ids we didn't get prices for

    def _worker():
        func, mids, myid = q.get()
        try:
            prices[myid], emids[myid] = func(mids)
        except URLError:
            # the nApi functions will raise URLError if there is no
            # network access etc.  There is a choice to be made here.
            # The 'safest' thing to do is to set emids to the complete
            # list of mids.  This will mean that all strategies (for
            # this exchange - either BDAQ or BF) will be removed by
            # the engine (see update_prices in managers.py).  Instead,
            # we can set prices to be an empty dict and emids to be an
            # empty list.  This won't remove the strategy.  
            prices[myid] = {}
            emids[myid] = []
        q.task_done()

    # start the threads: note we always start two threads here, even
    # when we are only fetching prices from either BDAQ or BF.
    for i in range(2):
        t = Thread(target = _worker)
        t.setDaemon(True)
        t.start()

    # tuple we put on the queue is function to call, argument, exid
    q.put((bdaqapi.GetPrices_nApi, middict[const.BDAQID], const.BDAQID))
    q.put((bfapi.GetPrices_nApi, middict[const.BFID], const.BFID))
    
    # block and wait for finish    
    q.join()

    return prices, emids

def _get_bf_orderlist(olist):
    
    odict = {}
    for o in olist:
        mid = o.mid
        if mid in odict:
            odict[mid].append(o)
        else:
            # start a new list for this mid
            odict[mid] = [o]
    
    # return a list of lists, where each sub-list is a list of orders
    # for a particular market id.  Note that this doesn't
    # (necessarily) preserve ordering, which is totally ok here.
    return odict.values()

def make_orders(ocancel, oupdate, onew):
    """Cancel/update/make new orders.

    ocancel - dict of orders to cancel
    oupdate - dict of orders to update
    onew    - dict of new orders to make

    Each dict has two, keys const.BDAQID, const.BFID, and items which
    are lists of order objects.

    We return three dictionaries corresponding to the output of
    cancelling, updating and making new orders.

    """

    q = Queue()
    # the order dictionaries we return
    corders = {const.BDAQID: {}, const.BFID: {}}
    uorders = {const.BDAQID: {}, const.BFID: {}}
    neworders = {const.BDAQID: {}, const.BFID: {}}

    def _worker():
        """
        Note this is a slightly different worker to the one used for
        update_prices above.  Also note that we are catching API
        errors...
        """

        func, olist, eid, rdict = q.get()
        try:
            ords = func(olist)
        except betexception.ApiError:
            print 'api error when placing following bets for id {0}:'.format(eid)
            print olist
            ords = {}

        # need to update since we may have more than one thread
        # for the BF bets.
        rdict[eid].update(ords)
        q.task_done()

    # list of order dictionary, BDAQ function, BF function, return
    # dictionary for cancelling, updating, and making new orders
    # respectively.
    ostuff = [[ocancel, bdaqapi.CancelOrders, bfapi.CancelBets, corders],
              [oupdate, bdaqapi.UpdateOrders, bfapi.UpdateBets, uorders],
              [onew, bdaqapi.PlaceOrdersNoReceipt, bfapi.PlaceBets, neworders]]

    for odict, bdaqfunc, bffunc, retdict in ostuff:

        # we start at most one thread for the BDAQ orders, since we
        # can place on multiple markets with a single API call
        if odict.get(const.BDAQID, []):
            bdaq_threads = 1
        else:
            bdaq_threads = 0

        # for BF, we need one API call for each separate market id.  So
        # first get a list of lists,
        # [[mid1_o1,mid1_o2,...],[mid2_o1,mid2_o2,...],...] Each list will
        # be given a single thread, and a BF API call.
        bf_betlist = _get_bf_orderlist(odict[const.BFID])

        # get list of lists, orders on each market.
        bf_threads = len(bf_betlist)
    
        # debug
        print 'number of bf_threads', bf_threads
        for olist in bf_betlist:
            print olist
    
        for i in range(bdaq_threads + bf_threads):
            t = Thread(target = _worker)
            t.setDaemon(True)
            t.start()

        # tuple we put on the queue is function to call, argument, exid
        if bdaq_threads:
            q.put((bdaqfunc, odict[const.BDAQID],
                   const.BDAQID, retdict))
        for i in range(bf_threads):
            q.put((bffunc, bf_betlist[i], const.BFID, retdict))
        
    # block and wait for finish
    q.join()

    return corders, uorders, neworders
