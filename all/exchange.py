# exchange.py
# James Mithen
# jamesmithen@gmail.com
#
# Event, Market, Selection objects

import const

class Event(object):
    """A top level event"""
    def __init__(self, name, myid, pid, pname=None):
        # convert name to ascii string and ignore any funky unicode
        # characters
        self.name = name.encode('ascii', 'ignore')
        self.id = myid
        # parent id
        self.pid = pid
        self.pname = pname

    def __repr__(self):
        return ' '.join([self.name, str(self.id)])

    def __str__(self):
        return self.__repr__()

class Market(object):
    """A market"""
    def __init__(self, name, myid, pid, inrunning, pname=None,
                 exid = const.BDAQID):
         # will need to change this when get BF going
        self.exid = exid
        # convert name to ascii string and ignore any funky unicode
        # characters
        self.name = name.encode('ascii', 'ignore')
        # from name, get event name, this is inside the first two |'s
        self.eventname =  self.name.split('|')[1]
        self.id = myid
        # parent id
        self.pid = pid
        self.pname = pname
        # is the market 'in running?'
        self.inrunning = inrunning

    def __repr__(self):
        return ' '.join([self.name, str(self.id)])

    def __str__(self):
        return self.__repr__()

class Selection(object):
    """A selection"""
    def __init__(self, name, myid, marketid, mback, mlay, lastmatched,
                 lastmatchedprice, lastmatchedamount, backprices,
                 layprices, exid=const.BDAQID):
        self.exid = exid
        # store everything that comes from bdaq API
        self.name = name
        self.id = myid # selection id
        self.mid = marketid # market id I belong to
        self.matchedback = mback        
        self.matchedlay = mlay        
        self.lastmatched = lastmatched
        self.lastmatchedprice = lastmatchedprice
        self.lastmatchedamount = lastmatchedamount

        # list of prices and stakes [(p1,s1), (p2,s2) ...,]
        self.backprices = backprices
        self.layprices = layprices

        # paded back and lay prices to const.NUMPRICES
        self.padback = self.PadPrices(backprices, const.NUMPRICES)
        self.padlay = self.PadPrices(layprices, const.NUMPRICES)

    def PadPrices(self, prices, num):
        """Pad prices so that if have fewer than num back or lay prices
        """
        nprices = len(prices)
        if nprices == num:
            return prices
        # pad prices with None
        app = [(None, None)] * (num - nprices)
        return prices + app

    def __repr__(self):
        return ' '.join([self.name, str(self.id)])

    def __str__(self):
        return self.__repr__()
