# for parsing dates from
        date = re.findall('\(.+\)', names[-3])[0][1:-1]
        # replace th and st in e.g. 13th September
        date = date.replace('th','')
        date = date.replace('st','')        
        print course, date, stime
        try:
            # convert date into datetime object
            dt = datetime.datetime.strptime(stime + ' ' + date,
                                            '%H:%M %d %B %Y')
        except:
            # there must not have been any time given
            print 'no time'
            pass
# for getting starttime of BF market from API(!)
    bfapi.Login()

    betlog.betlog.debug(('Checking market info for {0} BF markets '
                         'to match horse racing markets'.format(len(bfmarks))))
    minfo, emids = bfapi.GetMarketnonAPI([m.id for m in bfmarks])

    # use market info to update the market objects
    for m in bfmarks:
        # we might not have the info if it was one of the error mids
        if m.id in minfo:
            m.starttime = minfo[m.id]['marketTime']
            # numwinners should be 1 for all markets        
            m.numwinners = minfo[m.id]['numberOfWinners']
        else:
            # dummy starttime
            m.starttime = datetime.datetime(1,1,1)

    # if we are in BST (British Summer Time), then convert time to BST
    # (local) time from GMT.
    for m in bfmarks:
        m.starttime = m.starttime + datetime.timedelta(hours=1)


