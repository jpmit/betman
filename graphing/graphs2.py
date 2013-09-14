# graphs2.py
# James Mithen
# jamesmithen@gmail.com

# plot all historical price information for all matching selections

from betman import const, database
import matplotlib.pyplot as plt

dbman = database.DBMaster()

# get all matching selections
matchsels = dbman.ReturnSelectionMatches()

# go through each matching selection in turn and plot back and lay
# prices from each exchange
BDAQMARKETSWANTED = [3432804]

for msel in matchsels:
    # using BDAQ selection name
    selname = msel[0].name
    bdaqsid = msel[0].id
    bdaqmid = msel[0].mid    
    bfsid = msel[1].id
    bfmid = msel[1].mid    

    if bdaqmid not in BDAQMARKETSWANTED:
        continue

    # get BDAQ market name
    mname = dbman.cursor.execute(('SELECT market_name from markets '
                                  'where exchange_id = ? and '
                                  'market_id = ?'), (1, bdaqmid)).fetchall()[0][0]

    # get historical back and lay prices for both selections
    bfprices = dbman.cursor.execute(('SELECT b_1, lay_1, last_checked '
                                     'FROM histprices where '
                                     'exchange_id = ? and '
                                     'selection_id = ?'), (2, bfsid)).fetchall()
    bdaqprices = dbman.cursor.execute(('SELECT b_1, lay_1, last_checked '
                                     'FROM histprices where '
                                     'exchange_id = ? and '
                                     'selection_id = ?'), (1, bdaqsid)).fetchall()
    bfback = [s[0] for s in bfprices]
    bflay = [s[1] for s in bfprices]
    bdaqback = [s[0] for s in bdaqprices]
    bdaqlay = [s[1] for s in bdaqprices]
    
    # plot the selections, bo
    fig = plt.figure()
    ax = fig.add_subplot(111)
    ax.set_title(mname + " " + selname)
    ax.plot(bfback, 'ro')
    ax.plot(bfback, 'r')    
    ax.plot(bdaqback, 'r^')
    ax.plot(bdaqback, 'r--')        
    ax.plot(bflay, 'bo')
    ax.plot(bflay, 'b')    
    ax.plot(bdaqlay, 'b^')
    ax.plot(bdaqlay, 'b--')    
