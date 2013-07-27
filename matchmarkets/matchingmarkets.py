# matchingmarkets.py
# 21st July 2013
#
# go through database of markets, populate matching_markets with the
# ones that match, then for each market in turn, get the selection
# id's of all of the matching selections. Use this to populate
# matching_selections database.

import marketmatcher
import database
import const

dbman = database.DBMaster()

# these are exchange 1 (BDAQ) root names
names = ['Rugby Union', 'Formula 1', 'Soccer']

for name in names:
    # get all markets under this category
    BDAQMarkets = dbman.ReturnMarkets('SELECT * FROM markets where '
                                      'exchange_id=? and market_name LIKE ?',
                                      (const.BDAQID,'|{0}%'.format(name)))
    BFMarkets =  dbman.ReturnMarkets('SELECT * FROM markets where '
                                     'exchange_id=? and market_name LIKE ?',
                                     (const.BFID,'|{0}%'.format(name)))

    matches = marketmatcher.match(BDAQMarkets, BFMarkets, name)
    dbman.WriteMarketMatches(matches)
