# main2.py
# James Mithen
# jamesmithen@gmail.com
#
# Get markets from database
# This doesn't make any requests using the APIs

from betman import database
from betman.strategy.stratfunctions import crossmarket, is_lay_arb
from betman.matchmarkets.marketmatcher import GetMatchSelections

dbman = database.DBMaster()

# matching markets from database
mms = dbman.ReturnMarketMatches()

# get all selections in matching markets
sels1 = [dbman.ReturnSelections('SELECT * FROM selections where market_id = ?', (m[0].id,)) for m in mms]
sels2 = [dbman.ReturnSelections('SELECT * FROM selections where market_id = ?', (m[1].id,)) for m in mms]
msels = GetMatchSelections(sels1, sels2)

#for (i,m) in enumerate(mms):
#    print m[0].name
#    print m[1].name
#    print ','.join([m.name for m in msels[i][0]])
#    print ','.join([m.name for m in msels[i][1]])

# matching selections for these matching markets
#### TODO
# work on matching selections since we dont seem to be getting
# any selection matches for the soccer games in database!!!!!!!!
# (this despite having many matching markets)

msels2 = dbman.ReturnSelectionMatches()

# check if opportunity for betting
for s1, s2 in msels:
    is_lay_arb(s1, s2)
