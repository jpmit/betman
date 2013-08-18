# crossexchange.py
# James Mithen
# jamesmithen@gmail.com
#
# Classes for crossexchange strategy

import stratdata

# commission on winnings taken from both exchanges. The strategies can
# easily be generalised to the case when the commissions for BDAQ and
# BF are different.
_COMMISSION = 0.05

# CrossExchangeStrategy could maybe inherit from a general strategy
# class later on.
class CrossExchangeStrategy(object):
    def __init__(self, ex1sel, ex2sel):
        self.sel1 = ex1sel
        self.sel2 = ex2sel

        # self.opp stores whether there is a current betting
        # 'opportunity'.
        self.opp = False

    def _backlay(self, bprice, lprice):
        """Return True if back-lay strategy profitable, else False"""
        if bprice > lprice / ((1.0 - _COMMISSION)*(1.0 - _COMMISSION)):
            return True
        return False

    def _store_opportunity(self, slay, sback, olay, oback,
                           instant = False):
        """Store details of betting opportunity"""
        self.opp = True
        self.slay = slay
        self.sback = sback
        self.olay = olay
        self.oback = oback
        self.instant = False

    def print_opp(self):
        """Print details of opportunity"""
        pstr = 'Lay: {0} @ {1}, Back: {2} @ {3}'.format(self.slay.name,
                                                        self.olay,
                                                        self.sback.name,
                                                        self.oback)
        if self.instant:
            print 'INSTANT!' + pstr
        print pstr

    def check_opportunity(self):
        """Can I offer a better back than currently available, and then
        back on the other exchange at the current price?"""
        self.opp = False

        for s1,s2 in [(self.sel1,self.sel2), (self.sel2,self.sel1)]:
            # lay selection at best current price
            olay = s1.make_best_back()

            # back selection at best current price
            oback = s2.best_back()

            if self._backlay(oback, olay):
                self._store_opportunity(s1, s2, olay, oback)
                return True
        return False

    def check_instant_opportunity(self):
        """Can I back on one exchange and lay on the other exchange at
        prices that are currently on offer?"""
        self.opp = False

        for s1,s2 in [(self.sel1,self.sel2), (self.sel2,self.sel1)]:
            # lay selection at best current price
            olay = s1.best_lay()
            if olay == 1.0:
                # no lay price is currently offered
                return False

            # back selection at best current price
            oback = s2.best_back()

            if self._backlay(oback, olay):
                self._store_opportunity(s1, s2, olay, oback, True)
                return True
        return False
