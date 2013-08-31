# bdaqnonapiparse.py
# James Mithen
# jamesmithen@gmail.com
#
# Functions for parsing output of BDAQ non-API (webscraping) calls.

import json
import re
from betman import const, Selection

def ParsenonAPIGetPrices(resp, mids):
    """Return Selections for json string resp"""
    if const.DEBUG:
        print resp
    # get the raw data from BDAQ in a dictionary.
    jsondata = json.loads(correct_json(resp))

    # go through each market in turn and get the selections.  Note
    # there is more information returned than we are tracking here.
    allselections = []
    for (m,mark) in zip(mids, jsondata['ArrayOfEventClassifier']['EventClassifier']):
        # list of selections for this marketid
        allselections.append([])        
        # the mkt key contains everything we want
        for sel in mark['mkt']['sel']:
            name = sel['sN'].encode('ascii')
            sid = sel['sId']
            mid = sel['mId']
            # check that this is the marketid we were expecting
            assert (m == mid)
            if hasattr(sel, 'fSO'):
                bprices = [(p['p'], p['rA']) for p in sel['fSO']]
            else:
                bprices = []
            if hasattr(sel, 'aSO'):
                lprices = [(p['p'], p['rA']) for p in sel['aSO']]
            else:
                lprices = []

            # add the selection.  Note we are not getting amounts
            # matched etc. at the moment.
            allselections[-1].append(Selection(name, sid, mid,
                                               None,
                                               None,
                                               None,
                                               None,
                                               None,
                                               bprices, lprices))
    return allselections
    
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
