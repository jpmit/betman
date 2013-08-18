# exchange.py
# James Mithen
# jamesmithen@gmail.com
#
# Event, Market, Selection objects

import const
import exchangedata

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
        # store everything from BDAQ API below
        # convert name to ascii string and ignore any funky unicode
        # characters
        self.name = name.encode('ascii', 'ignore')        
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
        """Pad prices so that if have fewer than num back or lay
        prices"""
        nprices = len(prices)
        if nprices == num:
            return prices
        # pad prices with None
        app = [(None, None)] * (num - nprices)
        return prices + app

    def best_back(self):
        """Return best back price, or 1.0 if no price"""
        if self.backprices[0][0] is None:
            return exchangedata.MINODDS
        return max(exchangedata.MINODDS,
                   self.backprices[0][0])

    def best_lay(self):
        """Return best lay price, or 1000.0 if no price"""
        if self.layprices[0][0] is None:
            return exchangedata.MINODDS
        return min(exchangedata.MAXODDS,
                   self.layprices[0][0])

    def make_best_lay(self):
        """Return price for if we wanted to make a market on selection
        and be the best price on offer to lay.  E.g. if exchange is BF
        and best lay price is 21, this will return 20"""
        
        blay = self.best_lay()

        # design option: if the best back price is 1, we could return
        # None, but instead lets return 1.
        if blay == exchangedata.MINODDS:
            return exchangedata.MINODDS

        if self.exid == const.BDAQID:
            # use BDAQ betting increments
            if blay <= 3:
                return blay - 0.01
            elif blay <= 4:
                return blay - 0.05
            elif blay <= 6:
                return blay - 0.1
            elif blay <= 10:
                return blay - 0.2
            elif blay <= 20:
                return blay - 0.5
            elif blay <= 50:
                return blay - 1
            elif blay <= 200:
                return blay - 2
            elif blay <= 1000:
                return blay - 5

        elif self.exid == const.BFID:
            # use BF betting increments
            if blay <= 2 :
                return blay - 0.01
            elif blay <= 3:
                return blay - 0.02
            elif blay <= 4:
                return blay - 0.05        
            elif blay <= 6:
                return blay - 0.1
            elif blay <= 10:
                return blay - 0.2
            elif blay <= 20:
                return blay - 0.5
            elif blay <= 30:
                return blay - 1
            elif blay <= 50:
                return blay - 2
            elif blay <= 100:
                return blay - 5
            elif blay <= 1000:
                return blay - 10
        else:
            raise DataError, 'selection id must be either {0} or {1}'\
                  .format(const,BDAQID, const.BFID)

    def make_best_back(self):
        """Return price for if we wanted to make a market on selection
        and be the best price on offer to back E.g. if exchange is BF
        and best back price is 21, this will return 22."""

        bback = self.best_back()

        # design option: if the best lay price is 1000, we could
        # return None, but instead lets return 1000.
        if bback == exchangedata.MAXODDS:
            return exchangedata.MAXODDS
        if self.exid == const.BDAQID:
            # use BDAQ betting increments
            if bback < 3 :
                return bback + 0.01
            elif bback < 4:
                return bback + 0.05
            elif bback < 6:
                return bback + 0.1
            elif bback < 10:
                return bback + 0.2
            elif bback < 20:
                return bback + 0.5
            elif bback < 50:
                return bback + 1
            elif bback < 200:
                return bback + 2
            elif bback < 1000:
                return bback + 5

        elif self.exid == const.BFID:
            # use BF betting increments
            if bback < 2 :
                return bback + 0.01
            elif bback < 3:
                return bback + 0.02
            elif bback < 4:
                return bback + 0.05        
            elif bback < 6:
                return bback + 0.1
            elif bback < 10:
                return bback + 0.2
            elif bback < 20:
                return bback + 0.5
            elif bback < 30:
                return bback + 1
            elif bback < 50:
                return bback + 2
            elif bback < 100:
                return bback + 5
            elif bback < 1000:
                return bback + 10

        else:
            raise DataError, 'selection id must be either {0} or {1}'\
                  .format(const,BDAQID, const.BFID)

    def __repr__(self):
        return ' '.join([self.name, str(self.id)])

    def __str__(self):
        return self.__repr__()
