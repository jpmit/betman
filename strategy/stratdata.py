# stratdata.py
# James Mithen
# jamesmithen@gmail.com
#
# data for strategies

from betman import const, exchangedata

class StratError(Exception): pass

# Allowed odds for BDAQ data
# --------------------------
# Increments below obtained by testing betdaq.com on 4th August
# 1 	   3 	   0.01
# 3.05 	4 	   0.05
# 4.1 	6 	   0.1
# 6.2 	10 	0.2
# 10.5 	20 	0.5
# 21 	   50 	1
# 52     200   2
# 200    1000  5

# Allowed odds for BF data
# ------------------------
# Table below taken from
# http://help.betfair.info/contents/itemId/i65767327/index.en.html on
# 4th August 2013 : 
# From 	To 	Increment
# 1 	   2 	   0.01
# 2.02 	3 	   0.02
# 3.05 	4 	   0.05
# 4.1 	6 	   0.1
# 6.2 	10 	0.2
# 10.5 	20 	0.5
# 21 	   30 	1
# 32 	   50 	2
# 55 	   100 	5
# 110 	1000 	10
# 1000+ 	   Not Allowed
# The odds increment on Asian Handicap markets is 0.01 for all odds
# ranges.

def next_best_lay(sel):
    """Get 'next best lay price' for selection.  E.g. if exchange is
    BF and best BACK price is 21, this will return 22"""
    bback = sel.best_back()

    # design option: if the best lay price is 1000, we could return
    # None, but instead lets return 1000.
    if bback == exchangedata.MAXODDS:
        return exchangedata.MAXODDS
    if sel.exid == const.BDAQID:
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

    elif sel.exid == const.BFID:
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
        raise StratError, 'selection id must be either {0} or {1}'\
              .format(const,BDAQID, const.BFID)

def next_best_back(sel):
    """Get 'next best back price' for selection.  E.g. if exchange is
    BF and best lay price is 21, this will return 20"""
    blay = sel.best_lay()

    # design option: if the best back price is 1, we could return
    # None, but instead lets return 1.
    if blay == exchangedata.MINODDS:
        return exchangedata.MINODDS
    
    if sel.exid == const.BDAQID:
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

    elif sel.exid == const.BFID:
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
        raise StratError, 'selection id must be either {0} or {1}'\
              .format(const,BDAQID, const.BFID)
