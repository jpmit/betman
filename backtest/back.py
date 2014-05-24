import matplotlib.pyplot as plt
from betman import database

dbman = database.DBMaster()

mms = dbman.return_market_matches()

bdaqmids = [m[0].id for m in mms]

# load all time series data for all runners in both markets (last pair only).
mymid = 4028996
# get all selection matches for this mid
smatches = dbman.return_selection_matches([mymid])

fig1 = plt.figure()
fig2 = plt.figure()
ax1 = fig1.add_subplot(111)
ax2 = fig2.add_subplot(111)

for (s1, s2) in zip(smatches[0], smatches[1]):
    # time series data from betdaq
    pdata = dbman.return_selections('select * from histselections where exchange_id = ? '
                                    'and market_id = ? and selection_id = ?',
                                    (s2.exid, s2.mid, s2.id))
    # back price
    line, = ax1.plot_date([p.tstamp for p in pdata], [p.padback[0][0] for p in pdata], 
                          fmt='-')
    col = line.get_color()
    # lay price
    ax1.plot_date([p.tstamp for p in pdata], [p.padlay[0][0] for p in pdata], 
                  fmt='-', color=col)

    ax1.plot_date([p.tstamp for p in pdata], [p.padback[0][0] for p in pdata], 
                  marker='o', color=col)
    ax1.plot_date([p.tstamp for p in pdata], [p.padlay[0][0] for p in pdata], 
                  marker='o', color=col)

    
    print len(pdata)

    # time series data from bf
