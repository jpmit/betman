# bfnonapiparse.py
# James Mithen
# jamesmithen@gmail.com
#
# Functions for parsing output of BF non-Api (webscraping) calls.

import datetime
import xml.etree.ElementTree as etree
from betman import const, Selection, betlog
import json

# obsolete - do not use, use ParseJsonSelections instead
def ParseSelections(mids, xmlstr):
    root = etree.fromstring(xmlstr)
    selections = []
    # check we have one eventnode per mid in list
    enodes = root[0][1][0][0]
    return root
    #assert len(mids) == len(enodes)
    for mnum, enode in enumerate(enodes):
        selections.append([])
        # get one eventnode per market queried        
        for runner in enode[1][0][3]:
            name = runner[0][1].text
            sid = runner[3].text
            # exchange tag - this contains prices
            ex = runner[1]
            bprices = [(p[0].text, p[1].text) for p in ex[0]]
            lprices = [(p[0].text, p[1].text) for p in ex[1]]
            # add the selection to the list
            # we can fill in the things currently None later on...
            selections[mnum].append(Selection(name, sid, mids[mnum], None,
                                              None, None, None, None,
                                              bprices, lprices,
                                              const.BFID))
            
    # selections is a list of lists, e.g. selections[0] is a list
    # whose elements are Selection objects for the market with id
    # mids[0].
    return selections

def ParsenonAPIgetMarket(jstr, mids):
    """
    Parse json data, return market info as dictionary with mids as
    keys.
    """
    
    data = json.loads(jstr)

    # dictionary of dictionaries
    minfo = {}

    for event in data['eventTypes']:
        for eventnode in event['eventNodes']:
            for mkt in eventnode['marketNodes']:
                
                # take away the 1. or 2. at start of market id; this
                # corresponds to UK and AUS exchange respectively
                mid = int(mkt['marketId'].split('.')[1])

                stime = mkt['description']['marketTime']
                # convert the market starttime stime to a
                # datetime.datetime object.  stime should look like
                # '2014-03-11T15:20:00.000Z', so delete .000Z from end
                # of time and replace the 'T' with a space
                stime = stime[:-5].replace('T',' ')
                mtime = datetime.datetime.strptime(stime,
                                                   '%Y-%m-%d %H:%M:%S')
                
                # store dictionary with the info that we want here;
                # note there is more info that comes from the call
                # than we are storing here.
                minfo[mid] = {'marketName' : mkt['description']['marketName'],
                              'marketTime' : mtime,
                              'numberOfWinners' : mkt['state']['numberOfWinners']}

    # check how many markets we got market info for.
    # note, if we didn't get all markets, probably some have been
    # cancelled/finished etc.
    lminfo = len(minfo)
    lmids = len(mids)
    betlog.betlog.debug('BF got market info for {0} of {1} markets'\
                        .format(lminfo, lmids))

    # construct error list - market ids we did not get any market
    # information for. Presumably these have finished etc.
    errormids = []    
    if lminfo != lmids:
        for m in mids:
            if m not in minfo:
                errormids.append(m)

    if errormids:
        betlog.betlog.debug('BF no market info for markets: {0}'\
                            .format(' '.join([str(m) for m in errormids])))

    return minfo, errormids



def ParseJsonSelections(jstr, mids):
    """
    Parse json data, return selections as dictionary with mids as
    keys.
    """
    
    data = json.loads(jstr)

    # dictionary of dictionaries
    selections = {}
    for event in data['eventTypes']:
        for eventnode in event['eventNodes']:
            for market in eventnode['marketNodes']:
                
                # take away the 1. or 2. at start of market id; this
                # corresponds to UK and AUS exchange respectively
                mid = int(market['marketId'].split('.')[1])

                # dictionary of selections for this mid
                selections[mid] = {}
                
                for runner in market['runners']:
                    name = runner['description']['runnerName']
                    sid = runner['selectionId']
                    if 'availableToBack' in runner['exchange']:
                        back = [(b['price'], b['size']) for b in
                                runner['exchange']['availableToBack']]
                    else:
                        # no odds available to back
                        back = [(None, None)]
                    if 'availableToLay' in runner['exchange']:
                        lay = [(la['price'], la['size']) for la in
                               runner['exchange']['availableToLay']]
                    else:
                        # no odds available to lay
                        lay = [(None, None)]

                    selections[mid][sid] = Selection(const.BFID, name,
                                                     sid, mid,
                                                     None, None, None,
                                                     None, None, back,
                                                     lay, None, None,
                                                     **runner)

    # check how many markets we got selections for.
    # note, if we didn't get all markets, probably some have been
    # cancelled/finished etc.
    lsels = len(selections)
    lmids = len(mids)
    betlog.betlog.debug('BF got selections for {0} of {1} markets'\
                        .format(lsels, lmids))

    # construct error list - market ids we did not get any selection
    # information for. Presumably these have finished etc.
    errormids = []    
    if lsels != lmids:
        for m in mids:
            if m not in selections:
                errormids.append(m)

    if errormids:
        betlog.betlog.debug('BF no selections for markets: {0}'\
                            .format(' '.join([str(m) for m in errormids])))

    return selections, errormids
