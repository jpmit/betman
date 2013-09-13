# main.py
# James Mithen
# jamesmithen@gmail.com
#
# get markets from BDAQ and BF
# this makes requests using the APIs

from betman.api.bf import bfapi
from betman.api.bdaq import bdaqapi
import betman.matchmarkets.marketmatcher as marketmatcher
import betman.matchmarkets.matchconst as matchconst
from betman import database

dbman = database.DBMaster()
#dbman.cleanse()

# names for bf and bdaq need to map
bdaqelist = ['Horse Racing']#, 'Formula 1']#,'Baseball', 'Boxing', 'Cricket', 'Cycling']
bfelist = [matchconst.EVENTMAP[k] for k in bdaqelist]

# get top level events for BF and BDAQ
bdaqevents = bdaqapi.GetTopLevelEvents()
bfapi.Login()
bfevents = bfapi.GetActiveEvents()

# get markets for just a couple of event types
bdaqmarkets = bdaqapi.GetMarkets([ev.id for ev in bdaqevents
                                  if ev.name in bdaqelist])
bfmarkets = bfapi.GetUKMarkets([ev.id for ev in bfevents
                                if ev.name in bfelist])

# get matching markets: note, for horse racing, this takes a long time
# since it needs to call the BF API, which is heavily throttled.
matchmarks = marketmatcher.GetMatchMarkets(bdaqmarkets, bfmarkets)
bdaqmatches = [m[0] for m in matchmarks]
bfmatches = [m[1] for m in matchmarks]

# get selections for the markets that match.  Note f2or both apis (BF
# and BDAQ), we will get selections back in order called.
bfselections, bfemids = bfapi.GetSelections([m.id for m in bfmatches])
bdaqselections, bdaqemids = bdaqapi.GetSelectionsnonAPI([m.id for m in bdaqmatches])
# get matching selections for each selection in matching markets
matchsels = marketmatcher.GetMatchSelections(bdaqselections, bfselections)
