from betman import database

dbman = database.DBMaster()

mms = dbman.return_market_matches()

bdaqmids = [m[0].id for m in mms]

# load all time series data for all runners in both markets (last pair only).
for mymid in bdaqmids:
    # get all selection matches for this mid
    smatches = dbman.return_selection_matches([mymid])

    for (s1, s2) in zip(smatches[0], smatches[1])[:1]:
        # time series data from betdaq
        pdata = dbman.return_selections('select * from histselections where exchange_id = ? '
                                        'and market_id = ? and selection_id = ?',
                                        (s2.exid, s2.mid, s2.id))
        print len(pdata)

    # time series data from bf
