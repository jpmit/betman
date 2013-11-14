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


# multiprocessing (now replaced with multithreading)
# update prices from BDAQ API.
async_result = pool.apply_async(bdaqapi.GetPrices_nApi,
                                (self.marketids[const.BDAQID],))

# update prices from BF API. Note at the moment there doesn't
# seem to be a problem with requesting data for markets that
# have closed, but we may have to change this at a later date.
self.prices[const.BFID], bfemids = bfapi.GetPrices_nApi\
                                   (self.marketids[const.BFID])

self.prices[const.BDAQID], bdaqemids = async_result.get()

# multiprocessing for placing bets (again replaced by multithreading).
       
        if (odict[const.BDAQID]) and (odict[const.BFID]):
            # we are betting on both exchanges, so we use two
            # threads to send the orders simultaneously.
            pool = ThreadPool(processes=1)

            # place BDAQ order.
            bdaq_result = pool.apply_async(bdaqapi.PlaceOrdersNoReceipt,
                                           (odict[const.BDAQID],))

            # we can only place one bet (at least, only one mid) per
            # API call for BF
            nbfbets = len(odict[const.BFID])
            if nbfbets == 1:
                bfo = bfapi.PlaceBets(odict[const.BFID])
                saveorders[const.BFID].update(bfo)
            else:
                # more than one BF bet; (try to) place this
                # asynchronously
                bf_results = [None]*(nbfbets - 1)
                for bnum in range(nbfbets - 1):
                    bf_results[bnum] = pool.apply_async(bfapi.PlaceBets,
                                                        ([odict[const.BFID][bnum]],))
                bfo = bfapi.PlaceBets([odict[const.BFID][-1]])
                saveorders[const.BFID].update(bfo)
                
                # fetch the bf results
                for resp in bf_results:
                    d = resp.get()
                    saveorders[const.BFID].update(d)

            # fetch the BDAQ results
            bdo = bdaq_result.get()
            saveorders[const.BDAQID].update(bdo)

        else:
            # betting on BDAQ or BF or neither but not both - no
            # need for extra thread

            if odict[const.BDAQID]:
                # place the orders
                bdo = bdaqapi.PlaceOrders(odict[const.BDAQID])
                saveorders[const.BDAQID].update(bdo)
                # Annoying!  The BF API only allows us to make bets for
                # one market at a time (although we can make multiple bets
                # - up to 60 apparently - for each market.
            if odict[const.BFID]:
                for plorder in odict[const.BFID]:
                    bfo = bfapi.PlaceBets([plorder])
                    saveorders[const.BFID].update(bfo)
