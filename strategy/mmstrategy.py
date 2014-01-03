# mmstrategy.py
# James Mithen
# jamesmithen@gmail.com

"""Market making strategy."""

from betman.strategy import strategy

class MMStrategy(strategy.Strategy):
    """Market making strategy"""
    
    def __init__(self, ex1sel = None, ex2sel = None):
        super(CXStrategy, self).__init__()
