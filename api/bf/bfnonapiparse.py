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

def ParseJsonSelections(jstr, ids):
    """Parse json data, return selections SORTED BY LIST ids"""
    data = json.loads(jstr)
    # selections dictionary stores market id as key, list of
    # selections as value.
    selections = {}
    for event in data['eventTypes']:
        for eventnode in event['eventNodes']:
            for market in eventnode['marketNodes']:
                # take away the 1. or 2. at start of market id; this
                # corresponds to UK and AUS exchange respectively
                mid = int(market['marketId'].split('.')[1])
                # list of selections for this market
                selections[mid] = []
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
                    # create new selection for this market
                    selections[mid].append(Selection(name, sid, mid,
                                                     None, None, None,
                                                     None, None, back,
                                                     lay, const.BFID))
    # return selections ordered by list ids (passed as an argument).
    # this is so that when we call this function, we know what we are
    # getting back.  If we don't do this, we will get selections in an
    # order decided by BF, i.e. ordered by eventtype.
    allselections = [selections[mid] for mid in ids]
    return allselections


                    
    
    
