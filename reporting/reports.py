# reports.py
# James Mithen
# jamesmithen@gmail.com
#
# Diagnose trading P&L etc.

from betman import database, const

DATE = '2013-09-25'
EVENT = 'Horse Racing'

dbman = database.DBMaster()

# get matching orders
morder = dbman.ReturnOrderMatches(DATE)

# get all of the market ids of the orders
mids = {}

for (bdaqo, bfo) in morder:
    # each dictionary item (a list) will contain the market as the
    # first item, and a list of (bdaqorder, bdaqselection, bforder,
    # bfselection) for each matching order.
    mids[bdaqo.mid] = [None, []]

for (bdaqo, bfo) in morder:

    bdsel = dbman.ReturnSelectionById(const.BDAQID, bdaqo.mid, bdaqo.sid)
    bfsel = dbman.ReturnSelectionById(const.BFID, bfo.mid, bfo.sid)

    # save the BDAQ mid
    mids[bdaqo.mid][1].append((bdsel, bdaqo, bfsel, bfo))

# for all of the BDAQ market ids, get the BDAQ market
for m in mids:
    mids[m][0] = dbman.ReturnMarketById(const.BDAQID, m)

# remove the mids that are not the desired event
for k,v in mids.items():
    if v[0].eventname != EVENT:
        mids.pop(k)

    
