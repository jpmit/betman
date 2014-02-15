# multi.py
# James Mithen
# jamesmithen@gmail.com

"""Any multithreaded methods."""

from betman import const, betexception
from betman.api.bf import bfapi
from betman.api.bdaq import bdaqapi
from threading import Thread, active_count
from Queue import Queue

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
        prices[myid], emids[myid] = func(mids)
        q.task_done()

    # start the threads
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

def make_orders(odict):
    """
    Make orders.  Here oddict is a dictionary with keys
    const.BDAQID, const.BFID, and items which are the orders.
    Return dictionary of orders with the same keys.
    """

    q = Queue()
    orders = {const.BDAQID: {}, const.BFID: {}} # the orders

    def _worker():
        """
        Note this is a slightly different worker to the one used for
        update_prices above.  Also note that we are catching API
        errors...
        """

        func, olist, myid = q.get()
        try:
            ords = func(olist)
        except betexception.ApiError:
            print 'api error when placing following bets for id {0}:'.format(myid)
            print olist
            ords = {}
        # need to update since we may have more than one thread
        # for the BF bets.
        orders[myid].update(ords)
        q.task_done()

    # we start one thread for the BDAQ orders, since we can place on
    # multiple markets with a single API call
    if const.BDAQID in odict:
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
        q.put((bdaqapi.PlaceOrdersNoReceipt, odict[const.BDAQID],
               const.BDAQID))
    for i in range(bf_threads):
        q.put((bfapi.PlaceBets, bf_betlist[i], const.BFID))
        
    # block and wait for finish
    q.join()

    return orders
