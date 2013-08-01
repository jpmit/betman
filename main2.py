# main2.py
# James Mithen
# jamesmithen@gmail.com
#
# get markets from database

from betman import database

dbman = database.DBMaster()

mms = dbman.ReturnMarketMatches()
