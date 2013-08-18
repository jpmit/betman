# betmain.py
# James Mithen
# jamesmithen@gmail.com
#
# Main betting script.  Here we assume we have the matching markets
# and the matching selections already in the database (see main.py and
# main2.py), we just need to poll the prices regularly and check for
# any opportunities etc.

from betman import database
from betman.strategy.crossexchange import CrossExchangeStrategy

# database interface
dbman = database.DBMaster()

# get the matching selections
msels = dbman.ReturnSelectionMatches()

# create CrossExchangeStrategy object for every pair of matching
# selections.
cexs = []

for ms in msels:
    cexs.append(CrossExchangeStrategy(ms[0],ms[1]))

# check if there are any 'instant' opportunities (probably not).
for cex in cexs:
    if cex.check_opportunity() or cex.check_instant_opportunity():
        cex.print_opp()
