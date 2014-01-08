# position.py
# James Mithen
# jamesmithen@gmail.com

"""Class for monitoring net position for strategy."""

from betman import order

class PositionTracker(object):
    """Position tracker for a strategy involving a single selection."""
    
    def __init__(self, strategy):

        self.strategy = strategy
    
    def get_all_orders(self):
        """
        Return list of all orders the strategy has successfully placed
        (nb, these may or may not have been matched), ordered by time
        placed (oldest first).
        """

        return self.strategy.allorders

    def get_positions(self):
        """
        Return pos, posif for strategy.

        pos   - current position from matched orders
        posif - position if all orders were matched
        """

        pos = 0.0
        posif = 0.0
        for o in self.strategy.allorders:
            p = o.stake * o.price
            if o.polarity == order.LAY:
                p = -p
            posif += p
            if o.status == order.MATCHED:
                pos += p

        return pos, posif

    def get_unmatched_bets(self):

        unmatched = []
        for o in self.strategy.allorders:
            if o.status == order.UNMATCHED:
                unmatched.append(o)

        return unmatched

                
