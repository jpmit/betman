# stratfunctions.py
# James Mithen
# jamesmithen@gmail.com
#
# strategy functions

from betman import database
import stratdata

# commission on winnings taken from both exchanges. The strategies can
# easily be generalised to the case when the commissions for BDAQ and
# BF are different.
_COMMISSION = 0.05

def crossmarket(sel1, sel2):
    # print best back and best lay prices for each selection
    print sel1.name, sel1.best_back(), sel2.best_back()

def is_lay_arb(sel1, sel2):
    """Is arbitrage possible if I go best offer (lay better odds),
    then back on another exchange when hit?"""
    # try both ways round
    for s1,s2 in [(sel1,sel2), (sel2,sel1)]:
        # olay is the price we would post to lay at
        olay = stratdata.next_best_lay(s1)
        # when our lay is lifted, we would then turn to the other
        # exchange and buy back at oback
        oback = s2.best_back()
        if oback > olay/((1 - _COMMISSION)*(1 - _COMMISSION)):
            # then there is opportunity
            return True

def lay_arb_info(sel1, sel2):
    """Get lay arb info"""
    # get the market name and print it out:
    mark1 = database.DBMaster().ReturnMarkets('SELECT * FROM markets WHERE market_id = ?',
                                             (s1.mid,))[0]
    mark2 = database.DBMaster().ReturnMarkets('SELECT * FROM markets WHERE market_id = ?',
                                             (s2.mid,))[0]
    print mark1.name
    print mark2.name
    print olay, s1.name, s1.exid, oback



