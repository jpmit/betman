# order.py
# James Mithen
# jamesmithen@gmail.com

# Order objects for exchange

# BDAQ order _Status can be
# 1 - Unmatched.  Order has SOME amount available for matching.
# 2 - Matched (but not settled).
# 3 - Cancelled (at least some part of the order was unmatched).
# 4 - Settled.
# 5 - Void.
# 6 - Suspended.  At least some part unmatched but is suspended.
# here we use the same numbering scheme:
UNMATCHED = 1
MATCHED = 2
CANCELLED = 3
SETTLED = 4
VOID = 5
SUSPENDED = 6

class Order(object):
    """Returned after an order is placed"""
    def __init__(self, exid, sid, stake, price, polarity, **kwargs):
        self.exid = exid
        self.sid = sid
        self.stake = stake
        self.price = price
        self.polarity = polarity # 1 for back, 2 for lay

        for kw in kwargs:
            # notable kwargs (and therefore possible instance attributes) are:
            # oref - reference number from API
            # status - one of the numbers above e.g. MATCHED
            # matchedstake - amount of order matched
            # unmatchedstake - amount of order unmatched
            # strategy - integer for strategy number
            setattr(self, kw, kwargs[kw])

## class PlaceOrder(object):
##     """PlaceOrder holds info necessary to place an order"""
##     def __init__(self, exid, sid, stake, price, polarity):
##         self.exid = exid
##         self.sid = sid
##         self.stake = stake
##         self.price = price
##         self.polarity = polarity # 1 for back, 2 for lay
