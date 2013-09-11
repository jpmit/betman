# graphs.py
# James Mithen
# jamesmithen@gmail.com

from betman import const, database
import matplotlib.pyplot as plt

dbman = database.DBMaster()

mquery = ('SELECT DISTINCT histprices.exchange_id, histprices.market_id,'
          'markets.market_name FROM histprices INNER JOIN markets'
          ' ON histprices.market_id=markets.market_id')


marknums = dbman.cursor.execute(mquery).fetchall()

# selections
mnum =  110809729 # England vs Ukraine

sels = dbman.ReturnSelections(('SELECT * FROM selections where '
                               'market_id = 110809729'))

# historical prices for all selections

engprices = dbman.cursor.execute(('SELECT b_1, lay_1, last_checked FROM histprices where '
                                  'exchange_id = 2 and selection_id = 27')).fetchall()
engback = [s[0] for s in engprices]
englay = [s[1]  for s in engprices]
dates = [s[2] for s in engprices]
