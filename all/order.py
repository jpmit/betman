# order.py
# James Mithen
# jamesmithen@gmail.com

"""Order object for both exchanges."""

# BDAQ order _Status can be
# 1 - Unmatched.  Order has SOME amount available for matching.
# 2 - Matched (but not settled).
# 3 - Cancelled (at least some part of the order was unmatched).
# 4 - Settled.
# 5 - Void.
# 6 - Suspended.  At least some part unmatched but is suspended.
# here we use the same numbering scheme, but we add staus 'NOTPLACED'
# for our own internal use.
NOTPLACED = 0
UNMATCHED = 1
MATCHED = 2
CANCELLED = 3
SETTLED = 4
VOID = 5
SUSPENDED = 6
# polarity
BACK = 1
LAY = 2

class Order(object):
    """Used to place an order, and returned after an order is placed."""    
    
    def __init__(self, exid, sid, stake, price, polarity, **kwargs):
        """
        Create order from exid (const.BDAQID or const.BFID), selection
        id, stake (in GBP), price (odds), polarity (O_BACK or O_LAY).
        """
        
        self.exid = exid
        self.sid = sid
        self.stake = stake
        self.price = price
        self.polarity = polarity # 1 for back, 2 for lay

        # the following are defaults and can be overridden by **kwargs
        self.status = NOTPLACED
        # BDAQ only: cancel when market goes 'in running' aka 'in play'?
        self.cancelrunning = True
        # BF only: persistence type
        self.persistence = 'NONE'
        # BDAQ only: cancel if selection is reset?
        self.cancelreset = False
        # BDAQ only: selection reset count        
        self.src = 0
        # BDAQ only: withdrawal selection number        
        self.wsn = 0              

        for kw in kwargs:
            # notable kwargs (and therefore possible instance attributes) are:
            # not set at instantiation above:
            # oref           - reference number from API
            # matchedstake   - amount of order matched
            # unmatchedstake - amount of order unmatched
            # sname          - name of the selection that order is for
            # set at instantiation above (but sometimes overridden here):
            # status         - one of the numbers above e.g. O_MATCHED
            # cancelrunning  - default is True
            # cancelreset    - default is True
            # src            - selection reset count
            # wsn            - withdrawal sequence number

            setattr(self, kw, kwargs[kw])

    def __repr__(self):
        return '{0} {1} ${2} {3}'.format('BACK' if self.polarity == 1
                                         else 'LAY', self.sid,
                                         self.stake, self.price)

    def __str__(self):
        return self.__repr__()
