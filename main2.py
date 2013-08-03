# main2.py
# James Mithen
# jamesmithen@gmail.com
#
# get markets from database

from betman import database
from betman.strategy.stratfunctions import crossmarket

dbman = database.DBMaster()

# matching markets from database
mms = dbman.ReturnMarketMatches()

# matching selections for these matching markets
msels = dbman.ReturnSelectionMatches()

# check if opportunity for betting
for s1, s2 in msels:
    crossmarket(s1, s2)
