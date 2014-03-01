# matchingselections.py
# 22nd July 2013
#
# go through matchingmarkets database, get selections
# for each market from selection database, write matched
# selections to matchingselections table

from betman import database
from betman import const

dbman = database.DBMaster()

# Later there will be a clever way to do this using joins/views with
# tables matchingmarkets and markets...
# restrict to soccer games for now ...
mm = dbman.cursor.execute('SELECT * FROM matchingmarkets WHERE ex1_name LIKE ?',('%RBS%',)).fetchall()

m1ids = [m[0] for m in mm]
m2ids = [m[2] for m in mm]

# this market happens to be the six nations winner
sels1 = dbman.ReturnSelections('SELECT * FROM selections where market_id=?', (m1ids[0],))
sels2 = dbman.ReturnSelections('SELECT * FROM selections where market_id=?', (m2ids[0],))

# now insert matching selections into database
#dbman.WriteSelectionMatches(zip(sels1,sels2))
mm2 = dbman.cursor.execute('SELECT * FROM matchingselections').fetchall()
