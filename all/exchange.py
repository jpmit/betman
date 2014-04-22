# exchange.py
# James Mithen
# jamesmithen@gmail.com

"""Event, Market and Selection objects"""

import const
import exchangedata

class Event(object):
    """A top level event."""
    
    def __init__(self, name, myid, **kwargs):
        # convert name to ascii string and ignore any funky unicode
        # characters
        self.name = name.encode('ascii', 'ignore')
        self.id = myid

        # store all information that comes from the API
        self.properties = kwargs
        
    def __repr__(self):
        return ' '.join([self.name, str(self.id)])

    def __str__(self):
        return self.__repr__()

class Market(object):
    """A market."""
    
    def __init__(self, exid, name, myid, pid, inrunning, starttime,
                 totalmatched = None, **kwargs):

        # exchange ID, either const.BDAQID or const.BFID
        self.exid = exid
        # convert name to ascii string and ignore any funky unicode
        # characters
        self.name = name.encode('ascii', 'ignore')
        # from name, get event name, this is inside the first two |'s
        self.eventname =  self.name.split('|')[1]
        self.id = myid
        # parent id
        self.pid = pid
        # is the market 'in running?'
        self.inrunning = inrunning
        # time at which the market starts is not necessarily the time
        # it goes in running: e.g. for markets like Premiership winner
        # etc.
        self.starttime = starttime
        # total amount matched on market (note this defaults to None
        # and not 0.0).
        self.totalmatched = totalmatched

        # store all information that comes from the API
        self.properties = kwargs

    def __repr__(self):
        return ' '.join([self.name, str(self.id)])

    def __str__(self):
        return self.__repr__()

class Selection(object):
    """A selection."""
    
    def __init__(self, exid, name, myid, marketid, mback, mlay,
                 lastmatched, lastmatchedprice, lastmatchedamount,
                 backprices, layprices, src=None, wsn=None, dorder=None,
                 tstamp = None, **kwargs):

        self.exid = exid

        # convert name to ascii string and ignore any funky unicode
        # characters.
        self._uname = name
        self.name = name.encode('utf8')

        self.id = myid # selection id
        self.mid = marketid # market id I belong to
        self.matchedback = mback        
        self.matchedlay = mlay        
        self.lastmatched = lastmatched
        self.lastmatchedprice = lastmatchedprice
        self.lastmatchedamount = lastmatchedamount

        # selection reset count and withdrawal selection number are
        # used for BDAQ only.
        self.src = src
        self.wsn = wsn

        # display order is display order for BDAQ
        self.dorder = dorder

        # timestamp 
        self.tstamp = tstamp

        # list of prices and stakes [(p1,s1), (p2,s2) ...,]
        self.backprices = backprices
        self.layprices = layprices

        # paded back and lay prices to const.NUMPRICES
        self.padback = self.pad_prices(backprices, const.NUMPRICES)
        self.padlay = self.pad_prices(layprices, const.NUMPRICES)

        # store all data from API
        self.properties = kwargs

    def pad_prices(self, prices, num):
        """
        Pad prices so that if have fewer than num back or lay prices.
        """

        nprices = len(prices)
        if nprices == num:
            return prices
        # pad prices with None
        app = [(None, None)] * (num - nprices)
        return prices + app

    def best_back(self):
        """Return best back price, or 1.0 if no price."""
        
        if self.padback[0][0] is None:
            # this is 1.0
            return exchangedata.MINODDS

        return self.padback[0][0]

    def best_lay(self):
        """Return best lay price, or 1000.0 if no price."""
        
        if self.padlay[0][0] is None:
            # best lay is 1.01
            return exchangedata.MAXODDS

        return self.padlay[0][0]

    def make_best_lay(self):
        """
        Return price for if we wanted to make a market on selection
        and be the best price on offer to lay.  E.g. if exchange is BF
        and best lay price is 21, this will return 20.
        """
        
        blay = self.best_lay()

        # design option: if the best back price is 1, we could return
        # None, but instead lets return 1.
        #if blay == exchangedata.MINODDS:
        #    return exchangedata.MINODDS

        return exchangedata.next_shorter_odds(self.exid, blay)

    def make_best_back(self):
        """
        Return price for if we wanted to make a market on selection
        and be the best price on offer to back E.g. if exchange is BF
        and best back price is 21, this will return 22.
        """

        bback = self.best_back()

        # design option: if the best lay price is 1000, we could
        # return None, but instead lets return 1000.
        #if bback == exchangedata.MAXODDS:
        #    return exchangedata.MAXODDS

        return exchangedata.next_longer_odds(self.exid, bback)

    def __repr__(self):
        return ' '.join([self.name, str(self.id)])

    def __str__(self):
        return self.__repr__()
