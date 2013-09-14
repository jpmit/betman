# bdaqnonapiparse.py
# James Mithen
# jamesmithen@gmail.com
#
# Functions for parsing output of BDAQ non-API (webscraping) calls.

import json
import re
from betman import const, Selection, betlog
from betman.all.betexception import APIError

def ParsenonAPIGetPrices(resp, mids):
    """Return Selections for json string resp"""

    try:
        # get the raw data from BDAQ in a dictionary.
        jsondata = json.loads(correct_json(resp))
    except:
        # we will hopefully only reach here if we called this with a
        # single market id (i.e. mids is a list of length 1) AND the
        # market has finished. In this case we will get
        # 'EmptyResponse' (can check this easily in a browser).
        # Return no selections and the market ids
        return [[]], mids

    # go through each market in turn and get the selections.  Note
    # there is more information returned than we are tracking here.
    selections = {}

    jdata = jsondata['ArrayOfEventClassifier']['EventClassifier']
    # this is in case we queried price for a single market
    if isinstance(jdata, dict):
        jdata = [jdata]
    
    for mark in jdata:

        mdat = mark['mkt']
        
        # I think this is a bug where market information can be
        # returned twice.        
        if isinstance(mdat, list):
            mdat = mdat[0]

        # get market id
        markmid = mdat['mId']

        # list of selections for this marketid
        selections[markmid] = []
        # withdrawal selection number for the market; we store this in
        # the selection objects for speedier betting
        wsn = mdat['wSN']
        
        # the mkt key contains everything we want
        for sel in mdat['sel']:
            name = sel['sN'].encode('ascii')
            sid = sel['sId']
            # each selection also contains a market id.  This should
            # be the same as markmid above!
            mid = sel['mId']
            assert (mid == markmid)

            if 'fSO' in sel:
                # if there are multiple back prices available,
                # sel['fSO'] will be a list
                if isinstance(sel['fSO'], list):
                    bprices = [(p['p'], p['rA']) for p in sel['fSO']]
                else:
                    # only one back price available
                    bprices = [(sel['fSO']['p'], sel['fSO']['rA'])]
            else:
                # no back prices available
                bprices = []
                
            if 'aSO' in sel:
                # if there are multiple lay prices available,
                # sel['aSO'] will be a list                
                if isinstance(sel['aSO'], list):
                    lprices = [(p['p'], p['rA']) for p in sel['aSO']]
                else:
                    # only one lay price available
                    bprices = [(sel['aSO']['p'], sel['aSO']['rA'])]
            else:
                # no lay prices available
                lprices = []

            # selection recount number
            src = sel['sRC']

            # add the selection.  Note we are not getting amounts
            # matched etc. at the moment.
            selections[markmid].append(Selection(name, sid, mid,
                                                 None,
                                                 None,
                                                 None,
                                                 None,
                                                 None,
                                                 bprices, lprices,
                                                 src,
                                                 wsn))

    # check how many markets we got selections for.
    # note, if we didn't get all markets, probably some have been
    # cancelled/finished etc.
    betlog.betlog.debug('BDAQ got selections for {0} of {1} markets'\
                        .format(len(selections), len(mids)))
            
    # return selections ordered by list ids (passed as an argument).
    # this is so that when we call this function, we know what we are
    # getting back.  If we don't do this, we will get selections in an
    # order decided by BDAQ, i.e. ordered by eventtype.
    allselections = []
    errormids = []
    for mid in mids:
        if mid in selections:
            allselections.append(selections[mid])
        else:
            # we didn't manage to get any selections for this market,
            # presumably it is no longer available...
            allselections.append([])
            errormids.append(mid)

    if errormids:
        betlog.betlog.debug('BDAQ no selections for markets: {0}'\
                            .format(' '.join([str(m) for m in errormids])))

    # return selections and error mids, note len(selections) is
    # len(mids), but there will be empty lists for the error market
    # ids.
    return allselections, errormids
    
def correct_json(jstr):
    """
    Return proper Json from BDAQ response!  The problem with the
    Betdaq response is:
    (i) There are some spaces around the names
    (ii) None of the names are in double quotes
    """
    # Strip leading whitespace: match { followed by any number of
    # spaces followed by any alphanumeric character.
    jstr = re.sub(r"{\s*(\w)", r'{"\1', jstr)
    # Strip trailing whitespace: match , followed by any number of
    # spaces followed by any alphanumeric character
    jstr = re.sub(r",\s*(\w)", r',"\1', jstr)
    # Add double quotes: matches only an alphabetic character [a-zA-Z]
    # before the ":" and not any alphanumeric character \w, since we
    # don't want to match json values like 06:00 which are already in
    # double quotes.  Note: this assumes that all names from BDAQ end
    # with an alphabetic character (which seems to be the case).
    jstr = re.sub(r"([a-zA-Z]):", r'\1":', jstr)
    return jstr
