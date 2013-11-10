# main.py
# James Mithen
# jamesmithen@gmail.com

"""
Match markets and selections from BDAQ and BF.  This makes requests
using the APIs.
"""

import operator
from betman.api.bf import bfapi
from betman.api.bdaq import bdaqapi
import betman.matchmarkets.marketmatcher as marketmatcher
import betman.matchmarkets.matchconst as matchconst
from betman import database, const

# list of events (BDAQ names) that we are interested in.  See
# betman.matchmarkets.matchconst for list of possible names.
EVENT_NAMES = ['Soccer']

dbman = database.DBMaster()
#dbman.cleanse()

# names for bf and bdaq need to map
bdaqelist = EVENT_NAMES
bfelist = [matchconst.EVENTMAP[k] for k in bdaqelist]

# get top level events for BF and BDAQ
bdaqevents = bdaqapi.ListTopLevelEvents()
bfapi.Login()
bfevents = bfapi.GetActiveEventTypes()

# get markets for just a couple of event types
bdaqmarkets = bdaqapi.\
              GetEventSubTreeNoSelections([ev.id for ev in bdaqevents
                                           if ev.name in bdaqelist])
bfmarkets = bfapi.GetAllMarketsUK([ev.id for ev in bfevents
                                   if ev.name in bfelist])

# get matching markets: note, for horse racing, this takes a long time
# since it needs to call the BF API, which is heavily throttled.
matchmarks = marketmatcher.get_match_markets(bdaqmarkets, bfmarkets)
bdaqmatches = [m[0] for m in matchmarks]
bfmatches = [m[1] for m in matchmarks]
bfmids = [m.id for m in bfmatches]
bdaqmids = [m.id for m in bdaqmatches]

# get selection dictionary for the markets that match.  second
# argument here ensures we write to the database.
bfseldict, bfemids = bfapi.GetPrices_nApi(bfmids, True)
bdaqseldict, bdaqemids = bdaqapi.GetPrices_nApi(bdaqmids, True)

# get selections ordered by market
bfselections = [[bfseldict[m][s] for s in bfseldict[m]] for m in bfmids]
bdaqselections = [[bdaqseldict[m][s] for s in bdaqseldict[m]]
                  for m in bdaqmids]

# get matching selections for each selection in matching markets
matchsels = marketmatcher.get_match_selections(bdaqselections,
                                               bfselections)

# if we are interested in horse racing, write times of races to file
# (TODO: make this a bit cleaner).
if 'Horse Racing' in bdaqelist:
    horsematches = [m for m in bdaqmatches if hasattr(m, 'course')]
    horsematches.sort(key = operator.attrgetter('starttime'))
    wstr = ['{0} {1} {2}'.format(h.starttime, h.course, h.id)
            for h in horsematches]
    hfile = open(const.LOGDIR + '/horseraces.txt', 'w')
    hfile.write('DATE COURSE BDAQMARKETID\n{0}\n'.format('-'*32))
    hfile.write('\n'.join(wstr))
    hfile.close()
