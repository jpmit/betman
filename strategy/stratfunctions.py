# stratfunctions.py
# James Mithen
# jamesmithen@gmail.com
#
# strategy functions

# commission on winnings taken from both exchanges. The strategies can
# easily be generalised to the case when the commissions for BDAQ and
# BF are different.
_COMMISSION = 5.0

def crossmarket(sel1, sel2):
    # print best back and best lay prices for each selection
    print sel1.name, sel1.best_back(), sel2.best_back()

    
    
