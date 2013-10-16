# betmain2.py
# James Mithen
# jamesmithen@gmail.com

"""Main betting program."""

import time, datetime
import betman
from betman import const, database
from betman.api.bf import bfapi
from betman.api.bdaq import bdaqapi
from betman.all import betlog
import betutil
from multiprocessing.pool import ThreadPool

# in practicemode, we won't place any bets
PRACTICEMODE = False

# if this is set to false, we won't update any order info
UPDATEORDERINFO = True

class BetMain(object):
    def __init__(self, deltat):
        """deltat is time between price refreshes in seconds."""

        self.clock = betman.all.clock.Clock(deltat)
        self.dbman = database.DBMaster()
        
        self.load_strategies()
        
        # market ids for all strategies (for updating prices)
        self.marketids = self.stratgroup.get_marketids()

        # we store selection objects as a dictionary of dictionaries.
        # This contains the selection objects (e.g. a particular
        # horse), and the selection objects contain the current price,
        # hence the name.
        self.prices = {const.BDAQID: {}, const.BFID: {}}

        # orders for both exchanges
        self.orders = {const.BDAQID: {}, const.BFID: {}}

        # call the API functions to refresh prices etc.
        self.on_startup()

    def load_strategies(self):
        """Load strategies."""

        # load from pickle file
        try:
            sgroup = betutil.unpickle_stratgroup()
        except IOError:
            betlog.betlog.warn(('Could not read pickle file: attempting'
                                ' to read strategies from database'))
            # save strategies from DB to pickle file
            betutil.save_strategies()

            # load from the pickle file
            sgroup = betutil.unpickle_stratgroup()

        betlog.betlog.debug("Loaded {0} strategies".format(len(sgroup)))
        self.stratgroup = sgroup


    def update_market_prices(self):
        """
        Get new prices.  Here we use python's threading module to make
        the requests to BDAQ and BF (approximately) simultaneously.
        Note that we do not write selection information to the
        database here.
        """

        betlog.betlog.debug('Updating prices for {0} strategies'\
                            .format(len(self.stratgroup)))
        
        # market ids for all strategies (for updating prices)
        self.marketids = self.stratgroup.get_marketids()

        betlog.betlog.debug('BDAQ market ids total: {0}'.\
                            format(len(self.marketids[const.BDAQID])))
        
        betlog.betlog.debug('BF market ids total: {0}'.\
                            format(len(self.marketids[const.BFID])))

        pool = ThreadPool(processes=1)

        # update prices from BDAQ API.
        async_result = pool.apply_async(bdaqapi.GetSelectionsnonAPI,
                                        (self.marketids[const.BDAQID],))

        # update prices from BF API. Note at the moment there doesn't
        # seem to be a problem with requesting data for markets that
        # have closed, but we may have to change this at a later date.
        self.prices[const.BFID], bfemids = bfapi.GetSelections\
                                           (self.marketids[const.BFID])

        self.prices[const.BDAQID], bdaqemids = async_result.get()

        # remove any strategies from the strategy list that depend on
        # any of the BDAQ or BF markets in emids.
        if bdaqemids:
            self.stratgroup.remove_marketids(const.BDAQID, bdaqemids)
            self.marketids = self.stratgroup.get_marketids()
        
        if bfemids:
            self.stratgroup.remove_marketids(const.BFID, bfemids)
            self.marketids = self.stratgroup.get_marketids()

        # if we deleted any strategies, re-save the pickle so we only
        # load valid strategies at startup
        if bdaqemids or bfemids:
            betutil.pickle_stratgroup(self.stratgroup)

    def unmatched_orders(self, exid):
        """Return list of unmatched orders for exchange exid."""
        
        unmatched = []
        for o in self.orders[exid].values():
            if o.status == order.UNMATCHED:
                unmatched.append(o)
        return unmatched

    def update_order_information(self):
        """Get information on all current orders."""

        if (not PRACTICEMODE) and (UPDATEORDERINFO):
            # get list of unmatched orders on BDAQ
            bdaqunmatched = self.unmatched_orders(const.BDAQID)

            # only want to call BDAQ API if we have unmatched bets
            if bdaqunmatched:
                # this should automatically keep track of a 'sequence
                # number', so that we are updating information about all
                # orders.
                bdaqors = bdaqapi.ListOrdersChangedSince()
                self.orders[const.BDAQID].update(bdaqors)
            
            # get list of unmatched orders on BF
            bfunmatched = self.unmatched_orders(const.BFID)

            if bfunmatched:
                # we pass this function the list of order objects;
                bfors = bfapi.GetBetStatus(bfunmatched)
                # update order dictionary
                self.orders[const.BFID].update(bfors)

    def make_orders(self, odict = None):
        """Make outstanding orders for all strategies."""
        
        # get dictionary of outstanding orders for all strategies.
        # Keys are const.BDAQID and const.BFID
        if odict is None:
            odict = self.stratgroup.get_orders_to_place()
        saveorders = {const.BDAQID: {}, const.BFID: {}}

        if PRACTICEMODE:
            return

        if (odict[const.BDAQID]) or (odict[const.BFID]):
            betlog.betlog.debug('making orders: {0}'.format(odict))

        if (odict[const.BDAQID]) and (odict[const.BFID]):
            # we are betting on both exchanges, so we use two
            # threads to send the orders simultaneously.
            pool = ThreadPool(processes=1)

            # place BDAQ order.
            bdaq_result = pool.apply_async(bdaqapi.PlaceOrders,
                                           (odict[const.BDAQID],))

            # we can only place one bet (at least, only one mid) per
            # API call for BF
            nbfbets = len(odict[const.BFID])
            if nbfbets == 1:
                bfo = bfapi.PlaceBets(odict[const.BFID])
                saveorders[const.BFID].update(bfo)
            else:
                # more than one BF bet; (try to) place this
                # asynchronously
                bf_results = [None]*(nbfbets - 1)
                for bnum in range(nbfbets - 1):
                    bf_results[bnum] = pool.apply_async(bfapi.PlaceBets,
                                                        ([odict[const.BFID][bnum]],))
                bfo = bfapi.PlaceBets([odict[const.BFID][-1]])
                saveorders[const.BFID].update(bfo)
                
                # fetch the bf results
                for resp in bf_results:
                    d = resp.get()
                    saveorders[const.BFID].update(d)

            # fetch the BDAQ results
            bdo = bdaq_result.get()
            saveorders[const.BDAQID].update(bdo)

        else:
            # betting on BDAQ or BF or neither but not both - no
            # need for extra thread

            if odict[const.BDAQID]:
                # place the orders
                bdo = bdaqapi.PlaceOrders(odict[const.BDAQID])
                saveorders[const.BDAQID].update(bdo)
                # Annoying!  The BF API only allows us to make bets for
                # one market at a time (although we can make multiple bets
                # - up to 60 apparently - for each market.
            if odict[const.BFID]:
                for plorder in odict[const.BFID]:
                    bfo = bfapi.PlaceBets([plorder])
                    saveorders[const.BFID].update(bfo)

        # now save the order information to the DB.
        if (odict[const.BDAQID]) or (odict[const.BFID]):

            # update the dictionary of orders that we have placed
            # since starting the application; this
            self.orders[const.BDAQID].update(saveorders[const.BDAQID])
            self.orders[const.BFID].update(saveorders[const.BFID])

            # save the full order information to the DB
            self.save_orders(saveorders)

            # save the information on matching orders to the DB.  Note
            # we are assuming here that if the number of orders on
            # each exchange are the same, then orders are made of
            # matching orders.
            if (len(odict[const.BDAQID]) == len(odict[const.BFID])):
                self.save_match_orders(odict, saveorders)

    def save_match_orders(self, odict, saveorders):
        """Save matching order ids to database table matchorders."""

        # since we got odict from each strategy in turn, they
        # are already in matching order; we just need to add
        # the order refs that were returned by the BDAQ and BF
        # API.
        matchorders = zip(odict[const.BDAQID], odict[const.BFID])
        for (o1, o2) in matchorders:
            # we need to get the order id for o1 and o2 from
            # saveorders dictionary
            for o in saveorders[const.BDAQID].values():
                if o1.sid == o.sid and o1.mid == o.mid:
                    o1.oref = o.oref

            for o in saveorders[const.BFID].values():
                if o2.sid == o.sid and o2.mid == o.mid:
                    o2.oref = o.oref

        # write to DB
        self.dbman.WriteOrderMatches(matchorders,
                                     datetime.datetime.now())

    def save_orders(self, sorders):
        ords = [o.values() for o in sorders.values()]
        allords = [item for subl in ords for item in subl]

        # time we are writing is going to be a bit off
        self.dbman.WriteOrders(allords, datetime.datetime.now())

    def on_startup(self):
        # put all this stuff in __init__ eventually??
        
        # bootstrap BDAQ order information (we don't need to do this
        # for BF).
        ords = bdaqapi.ListBootstrapOrders()
        while ords:
            ords = bdaqapi.ListBootstrapOrders()

        # need to login to BF api (we don't need to do this for BF).
        bfapi.Login()

        #  update market prices
        self.update_market_prices()

    def save_prices(self):
        """
        Save prices of all selections in self.prices dictionary to DB.
        """
        
        # could be a quicker way of getting flat selection list in
        # api/bf/bfnonapimethod.py
        allsels = []
        for exmid in self.prices:
            for mid in self.prices[exmid]:
                for sel in self.prices[exmid][mid]:
                    allsels.append(self.prices[exmid][mid][sel])

        # note that the time we are writing is going to be a bit off
        self.dbman.WriteSelections(allsels, datetime.datetime.now())

    def main_loop(self):

        # first tick initializes clock
        self.clock.tick()

        # second tick waits for the allocated time
        self.clock.tick()
        
        while True:
            # print intro stuff
            print time.asctime()
            print '-'*32

            # update fill status of orders etc
            self.update_order_information()
            
            # call BF and BDAQ API functions to get prices for all
            # relevant markets
            self.update_market_prices()
            
            # update the strategies: based on the most recent prices,
            # do the thinking, and create/cancel orders.
            self.stratgroup.update(self.prices)

            # make any outstanding orders and save order info.
            self.make_orders()

            # before next loop, save the updated prices.
            self.save_prices()
            
            self.clock.tick()
        
if __name__=='__main__':
    bm = BetMain(1)
    bm.main_loop()
