import xml.etree.ElementTree as etree
from betman import const, Selection
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

def ParseJsonSelections(jstr):
    """Parse json data, return selections SORTED BY MARKET ID"""
    data = json.loads(jstr)
    selections = []
    mids = []
    mnum = 0
    for event in data['eventTypes']:
        for eventnode in event['eventNodes']:
            for market in eventnode['marketNodes']:
                # take away the 1. or 2. at start of market id; this
                # corresponds to UK and AUS exchange respectively
                mid = market['marketId'].split('.')[1]
                mids.append(mid)
                # list of selections for this market
                selections.append([])
                for runner in market['runners']:
                    name = runner['description']['runnerName']
                    sid = runner['selectionId']
                    if 'availableToBack' in runner['exchange']:
                        back = [(b['price'], b['size']) for b in
                                runner['exchange']['availableToBack']]
                    if 'availableToLay' in runner['exchange']:
                        lay = [(la['price'], la['size']) for la in
                               runner['exchange']['availableToLay']]
                    # create new selection for this market
                    selections[mnum].append(Selection(name, sid, mid,
                                                      None, None, None,
                                                      None, None, back,
                                                      lay, const.BFID))

                # next market
                mnum = mnum + 1
    # sort selections by market id.  this is so that when we call this
    # function, we know what we are getting back.  If we don't do
    # this, we will get selections in an order decided by BF,
    # i.e. ordered by eventtype.
    mids, selections = zip(*sorted(zip(mids, selections)))
    return list(selections)

                    
    
    
