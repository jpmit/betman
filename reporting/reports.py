# reports.py
# James Mithen
# jamesmithen@gmail.com
#
# Diagnose trading P&L etc.

from betman import database

date = '2013-09-21'
dbman = database.DBMaster()
allorders = dbman.cursor.execute(("SELECT * FROM orders where tstamp "
                                  "like'{0}%'").format(date))\
                                  .fetchall()
