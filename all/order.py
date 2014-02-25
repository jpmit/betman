# order.py
# James Mithen
# jamesmithen@gmail.com

"""Order object for both exchanges."""

from betman.all import const
from betman.all.betexception import InternalError

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

# mapping of order number to order status
STATUS_MAP = {0: 'Not Placed',
              1: 'Unmatched',
              2: 'Matched',
              3: 'Cancelled',
              4: 'Settled',
              5: 'Void',
              6: 'Suspended'}
# mapping of polarity to name
POLARITY_MAP = {1: 'BACK',
                2: 'LAY'}

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
            # persistence    - same as cancelrunning but for BF
            # deltastake     - change to make to stake when updating (BDAQ only)
            # newpersistence - for updating (BF only)
            # newprice       - for updating (BF only)
            # newstake       - for updating (BF only)
            # tupdated       - the API parsing functions store the time 
            #                  returned from BDAQ/BF API here.
            # tplaced        - the API parsing functions store the time 
            #                  returned from BDAQ/BF API here.

            setattr(self, kw, kwargs[kw])

    def update(self, price=None, stake=None, persistence=None):
        """Set new price and new stake, ready for the order to be updated on
        either BF or BDAQ.

        This method encapsulates the exact details of the APIs.  Note
        that newpersistence can be used for BF only.

        """

        if (self.exid == const.BDAQID):
            if price is not None:
                self.price = price
                self.deltastake = 0.0
            if stake is not None:
                self.deltastake = stake - self.stake

        elif (self.exid == const.BFID):
            # set new values to old values, then overwrite
            self.newprice = self.price
            self.newstake = self.stake
            self.newpersistence = self.persistence
            # For BF, we need to keep track of original price, stake
            # and persistence since the BF API needs this information.
            if price is not None:
                self.newprice = price
                # note we can't update price and stake simultaneously
                # (if we try to, the new size is ignored!), so raise
                # an exception if we try to do this.
                if stake is not None:
                    raise InternalError, ('can\'t update price and '
                                          'stake of order simultaneously')
            if stake is not None:
                self.newstake = stake
            if persistence is not None:
                self.newpersistence = persistence
        else:
            raise InternalError, 'exchange ID {0} unknown'.format(self.exid)

    def __repr__(self):
        return '{0} {1} ${2} {3}'.format('BACK' if self.polarity == 1
                                         else 'LAY', self.sid,
                                         self.stake, self.price)

    def __str__(self):
        return self.__repr__()
