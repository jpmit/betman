# main2.py
# James Mithen
# jamesmithen@gmail.com
#
# get markets from database

from betman import database
from betman.strategy.stratfunctions import crossmarket, is_lay_arb

dbman = database.DBMaster()

# matching markets from database
mms = dbman.ReturnMarketMatches()

# matching selections for these matching markets
#### TODO
# work on matching selections since we dont seem to be getting
# any selection matches for the soccer games in database!!!!!!!!
# (this despite having many matching markets)
msels = dbman.ReturnSelectionMatches()

# check if opportunity for betting
for s1, s2 in msels:
    is_lay_arb(s1, s2)
