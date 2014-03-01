"""OrderStore and PriceStore.

These classes do all the bookkeeping for the orders
made/updated/cancelled and the prices for the markets.  They are
accessed by the OrderManager and PricingManager (see
managers.py). They also handle writing order and price information to
the database.

One reason for the existence of these objects is that we can keep
everything in memory.

"""

from betman import const, database, order, util
from singleton import Singleton
#from models import AbstractModel

@Singleton
class PriceStore(object):
    # not yet implemented
    pass

@Singleton
class OrderStore(object):
    """Model for storing information on orders made.

    Note this model encapsulates the data for ALL orders, not just a
    single order.

    """

    def __init__(self):

        # the current state of all orders placed since the start of
        # the application.  The keys to each sub-dictionary are the
        # order ids, with values that are the order objects. Note each
        # order object will typically be updated multiple times.
        self._orders = {const.BDAQID: {}, const.BFID: {}}

        # the state of all orders immediately after they were placed.
        # Among other things, these order objects are useful since
        # they have a 'tplaced' attribute.
        self._neworders = {const.BDAQID: {}, const.BFID: {}}

        # store mapping of order ref to time placed.
        self._tplaced = {const.BDAQID: {}, const.BFID: {}}

        # the state of all orders immediately after they were placed.
        self._cancelorders = {const.BDAQID: {}, const.BFID: {}}

        # for writing to database
        self._dbman = database.DBMaster()

        # store dicts of cancelled, updated and new orders placed by
        # the APIs from the latest tick.
        self.latest = [{const.BDAQID: {}, const.BFID: {}}, 
                       {const.BDAQID: {}, const.BFID: {}}, 
                       {const.BDAQID: {}, const.BFID: {}}]

        # store dict of updated orders from last tick (from querying
        # order status via the API).
        self.latest_updates = {const.BDAQID: {}, const.BFID: {}}

    def get_tplaced(self, o):
        """Return time placed (a datetime.datetime object_ for order o."""

        return self._tplaced[o.exid][o.oref]

    def get_order(self, exid, oref):
        """Return current state of an order, or None if no order found

        exid - exchange id (either const.BDAQID or const.BFID)
        oref - order reference of order as initially placed

        This method is typically called by strategy objects. Note a
        bit of magic happens here to get around the fact that updating
        orders on BF tends to produce additional orders with new
        orefs, but new orders are not produced on BDAQ.

        """
        
        if exid == const.BDAQID: # easy!
            return self._orders[exid].get(oref)

        else:
            # TODO: make things work properly for BF...
            return self._orders[exid].get(oref)   

    def set_tplaced(self, olist):
        """Set time placed for every order in olist."""

        for o in olist:
            if not hasattr(o, 'tplaced'):
                o.tplaced = self._tplaced[o.exid][o.oref]

    def get_orders_from_oref_dict(self, orefdict):
        bdolist = map(self.get_order, [const.BDAQID]*len(orefdict[const.BDAQID]),
                      orefdict[const.BDAQID])
        bfolist = map(self.get_order, [const.BFID]*len(orefdict[const.BFID]), 
                      orefdict[const.BFID])

        return {const.BDAQID: bdolist, const.BFID: bfolist}

    def get_current_orders(self, exid):
        return self._orders[exid]

    def add_orders(self, corders, uorders, neworders):

        """Add cancel, update and new order dicts to the store.

        corders   - dictionary of cancelled orders with keys const.BDAQID and
                    const.BFID, values that are lists of order objects.
        uorders   - dictionary of updated orders with keys const.BDAQID and
                    const.BFID, values that are lists of order objects.
        neworders - dictionary of new orders with keys const.BDAQID and
                    const.BFID, values that are lists of order objects.

        """

        if corders:
            self.add_cancel_orders(corders)

        if uorders:
            self.add_update_orders(uorders)
        
        if neworders:
            self.add_new_orders(neworders)

        # we store the cancelled, updated and new orders in a list
        # every time.
        self.latest = [corders, uorders, neworders]

    def add_cancel_orders(self, odict):
        """Add cancelled orders to the store.

        odict - dictionary of orders with keys const.BDAQID and
                const.BFID, values that are lists of order objects.

        """

        # add to cancel orders dictionary
        self._cancelorders[const.BDAQID].update(odict.get(const.BDAQID, {}))
        self._cancelorders[const.BFID].update(odict.get(const.BFID, {}))

        # update the current order state dictionary
        self._orders[const.BDAQID].update(odict.get(const.BDAQID, {}))
        self._orders[const.BFID].update(odict.get(const.BFID, {}))

        # save to DB
        ords = [o.values() for o in odict.values()]
        allords = [item for subl in ords for item in subl]
        self._dbman.write_orders(allords)

    def add_new_orders(self, odict):
        """Add newly placed orders to the store.  

        odict   - dictionary of orders with keys const.BDAQID and
                  const.BFID, values that are lists of order objects.

        Note the orders in odict need to have already been placed
        using the BDAQ and/or BF API (otherwise we won't have an order
        id).

        """

        # add to new orders dictionary
        self._neworders[const.BDAQID].update(odict.get(const.BDAQID, {}))
        self._neworders[const.BFID].update(odict.get(const.BFID, {}))

        # update the current order state dictionary
        self._orders[const.BDAQID].update(odict.get(const.BDAQID, {}))
        self._orders[const.BFID].update(odict.get(const.BFID, {}))

        # get flat list of all order objects
        ordlist = util.flattendict(odict)

        # store time placed
        for o in ordlist:
            self._tplaced[o.exid][o.oref] = o.tplaced

        # write to DB
        self._dbman.write_orders(ordlist)

    def add_update_orders(self, odict):
        """Add updated orders to the store.

        odict - dictionary of orders with keys const.BDAQID and
                const.BFID, values that are lists of order objects.

        Warning: this is easy for BDAQ, but quite tricky for BF, since
        updating BF orders may or may not produce extra orders.

        """

        # add the moment, this method doesn't support raising the
        # stake in BF.  Therefore, the currently supported method of
        # upping the stake for BF is to cancel the bet and then place
        # a new one at the larger stake.  For all other order updates,
        # we should be ok here.

        pass

    def get_unmatched_orders(self, exid):
        """Return list of unmatched orders for exchange exid."""
        
        unmatched = []
        for o in self._orders[exid].values():
            if o.status == order.UNMATCHED:
                unmatched.append(o)
        return unmatched

    def process_order_updates(self, exid, odict, ounmatched):
        """Process updating status of currently existing orders.

        Here we are processing the results of call to
        ListOrdersChangedSince (BDAQ) or GetBetStatus (BF).

        exid       - either const.BDAQID or const.BFID
        odict      - dictionary of order objects received from API (BF/BDAQ)
        ounmatched - LIST of order objects unmatched on the exchange (BF/BDAQ)
        tupdated   - the time of the update

        """

        if (exid == const.BFID):
            # since we use GetMUBets for getting BF bet status, we
            # won't return any cancelled/voided orders.  But we will
            # still be tracking them in this order model as being
            # unmatched.  Therefore, we need to remove these orders
            # from our internal tracker self._orders (specifically, we
            # set their status to order.CANCELLED).  Note this is the
            # method BF recommends for application developers (see p85
            # of the reference guide).
            unmatcheddict = {o.oref: o for o in ounmatched}
            for oid in unmatcheddict:
                if oid not in odict:
                    print 'order id {0} was CANCELLED'.format(oid), self._orders[exid][oid]
                    self._orders[exid][oid].status = order.CANCELLED

        # next, for all of the orders we got back from either BDAQ or
        # BF, we want to put in the market id, since this information
        # isn't returned by the API.
        
                                        
        # update main order dictionary
        self._orders[exid].update(odict)

        # refresh latest update dict
        self.latest_updates[exid] = odict
