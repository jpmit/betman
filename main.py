# main.py
# James Mithen
# jamesmithen@gmail.com
#
# get markets from BDAQ and BF

from betman.api.bf import bfapi
from betman.api.bdaq import bdaqapi
import betman.matchmarkets.marketmatcher as marketmatcher

# names for bf and bdaq need to map
bdaqelist = ['Rugby Union', 'Formula 1']
bfelist = ['Rugby Union', 'Motor Sport']

# get top level events for BF and BDAQ
bdaqevents = bdaqapi.GetTopLevelEvents()
bfapi.Login()
bfevents = bfapi.GetActiveEvents()

# get markets for just a couple of event types
bdaqmarkets = bdaqapi.GetMarkets([ev.id for ev in bdaqevents
                                  if ev.name in bdaqelist])
bfmarkets = bfapi.GetUKMarkets([ev.id for ev in bfevents
                                if ev.name in bfelist])

# get matching markets for each event in order
matchms = []
for (n1, n2) in zip(bdaqelist, bfelist):
    bdaqms = [m for m in bdaqmarkets if m.geteventname() == n1]
    bfms = [m for m in bfmarkets if m.geteventname() == n2]
    print bdaqms, bfms
    matchms += (marketmatcher.match(bdaqms, bfms, n1))

# get matching selections for each selection in matching markets
selectionmatcher.match(matchms)
