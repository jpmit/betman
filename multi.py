# multi.py
# James Mithen
# jamesmithen@gmail.com

"""Any multithreaded methods."""

from betman import const, betexception
from betman.api.bf import bfapi
from betman.api.bdaq import bdaqapi
from threading import Thread
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
        while True:
            func, mids, myid = q.get()
            prices[myid], emids[myid] = func(mids)
            q.task_done()

    # start the thread
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

def make_orders(odict):
    """
    Make orders.  Here oddict is a dictionary with keys
    const.BDAQID, const.BFID, and items which are the orders.
    Return dictionary of orders with the same keys.
    """

    q = Queue()
    orders = {} # the orders

    def _worker():
        """
        Note this is a slightly different worker to the one used for
        update_prices above.  Also note that we are catching API
        errors...
        """
        
        while True:
            func, mids, myid = q.get()
            try:
                ords = func(mids)
            except betexception.ApiError:
                ords = {}
            # need to update since we may have more than one thread
            # for the BF bets.
            orders.update(ords)
            q.task_done()

    # we start one thread for the BDAQ orders, and one thread for each
    # of the BF orders.  Note that this is not quite optimum, since in
    # principle a single BF call can place multiple bets on a single
    # market.  So if some of the BF orders are for the same market, we
    # are missing a trick...
    bdaq_threads = 1 if odict[const.BDAQID] else 0
    bf_threads = len(odict[const.BFID])
    
    for i in range(bdaq_threads + bf_threads):
        t = Thread(target = _worker)
        t.setDaemon(True)
        t.start()

    # tuple we put on the queue is function to call, argument, exid
    if bdaq_threads:
        q.put((bdaqapi.PlaceOrdersNoReceipt, odict[const.BDAQID],
               const.BDAQID))
    for i in range(bf_threads):
        q.put((bfapi.PlaceBets, odict[const.BFID], const.BFID))
        
    # block and wait for finish
    q.join()

    return orders
