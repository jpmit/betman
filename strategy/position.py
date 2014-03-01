# position.py
# James Mithen
# jamesmithen@gmail.com

"""Class for monitoring net position for strategy."""

from betman import const, order, util
from operator import attrgetter
from betman.core import stores

class PositionTracker(object):
    """Position tracker for a strategy involving a single selection."""
    
    def __init__(self, strategy):

        self.strategy = strategy

        self.ostore = stores.OrderStore.Instance()
    
    def get_all_orders(self):
        """
        Return list of all orders the strategy has successfully placed
        (nb, these may or may not have been matched), ordered by time
        placed (oldest first).
        """
        
        # dictionary of order references
        orefdict = self.strategy.get_allorefs()
        
        # dictionary of the actual order objects
        odict = self.ostore.get_orders_from_oref_dict(orefdict)

        # get a single list of order objects ordered by time placed
        olist = util.flatten(odict)
        self.ostore.set_tplaced(olist)
        olist.sort(key=attrgetter('tplaced'))

        return olist

    def get_positions(self):
        """
        Return pos, posif for strategy.

        pos   - current position from matched orders
        posif - position if all orders were matched
        """

        # what we want is (i) our return if the selection wins and
        # (ii) our return if the selection loses.  We want this in two
        # cases: (i) currently (i.e. with the current set of unmatched
        # bets) and (ii) if all of the bets made are matched.  So we
        # have 4 numbers.

        win_pos = 0.0
        win_posif = 0.0
        lose_pos = 0.0
        lose_posif = 0.0
        
        
        for o in self.get_allorders():
            # add this to all positions
            if o.status == order.MATCHED:
                if o.polarity == order.LAY:
                    dw = -o.stake * o.price
                    dl = o.stake
                else: # back
                    dw = o.stake * o.price
                    dl = -o.stake
                win_pos += dw
                lose_pos += dl
                win_posif += dw
                lose_posif += dl
            elif o.status == order.UNMATCHED:
                # careful here, since the order could be 'part'
                # matched.
                ms, us = o.matchedstake, o.unmatchedstake
                # compute win/loss amounts for matched and unmatched
                # parts separately.
                if o.polarity == order.LAY:
                    dwm = -ms * o.price
                    dwu = -us * o.price
                    dlm = ms
                    dlu = us
                else: # back
                    dwm = ms * o.price
                    dwu = us * o.price
                    dlm = -ms
                    dlu = -us
                win_pos += dwm
                lose_pos += dlm
                win_posif += dwm + dwu
                lose_posif += dlm + dlu

        return win_pos, win_posif, lose_pos, lose_posif

    def get_unmatched_bets(self):

        unmatched = []
        for o in self.get_allorders():
            if o.status == order.UNMATCHED:
                unmatched.append(o)

        return unmatched
                
    def get_all_bets(self):
        return self.strategy.get_allorders()
