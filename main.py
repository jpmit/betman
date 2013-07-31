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
bfelist = [marketmatcher.EVENTMAP[k] for k in bdaqelist]

# get top level events for BF and BDAQ
bdaqevents = bdaqapi.GetTopLevelEvents()
bfapi.Login()
bfevents = bfapi.GetActiveEvents()

# get markets for just a couple of event types
bdaqmarkets = bdaqapi.GetMarkets([ev.id for ev in bdaqevents
                                  if ev.name in bdaqelist])
bfmarkets = bfapi.GetUKMarkets([ev.id for ev in bfevents
                                if ev.name in bfelist])

# get matching markets
matchmarks = marketmatcher.GetMatchMarkets(bdaqmarkets, bfmarkets)
bdaqmatches = [m[0] for m in matchmarks]
bfmatches = [m[1] for m in matchmarks]

##### TO DO - FIX GETSELECTIONS for BF (and maybe also for bdaq)
##### XML returns Eventnode -> marketnode ->
##### the data returned is sorted first by event id, then by market it
##### we need to take this into account!!!
# get selections for the markets that match
bfselections = bfapi.GetSelections([m.id for m in bfmatches])
bdaqselections = bdaqapi.GetSelections([m.id for m in bdaqmatches])
# get matching selections for each selection in matching markets
selectionmatcher.match(matchms)
