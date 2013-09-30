# reports.py
# James Mithen
# jamesmithen@gmail.com
#
# Diagnose trading P&L etc.

from betman import database, const
from operator import itemgetter
import getwinner

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

# get the market names and ids
mnamesids = [(m[0].name.split('|')[-2], m[0].id) for m in mids.values()]
# this should sort the market names into time order
mnamesids = sorted(mnamesids, key=itemgetter(0))
# get the winners from the BBC website
#winners = getwinner.getwinners(DATE, mnames)

# go through each item in list mnamesids.
# the heading of the table should be mnamesids[0].
# then loop through all orders
from django.conf import settings
from django import template
from django.template.loader import get_template
settings.configure(DEBUG=True, TEMPLATE_DEBUG=True, TEMPLATE_DIRS=('.', ))

t = get_template('results.html')
c = template.Context({'namesandids' : mnamesids, 'info': mids})
html = t.render(c)

sfile = open('test.html', 'w')
sfile.write(html)
sfile.close()

