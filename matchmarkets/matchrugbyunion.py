# matchmarkets.py
# 18th July 2013
# Try to match markets between BF and BDAQ (!)

import database
import const
import numpy as np
import re

def level2convert(s):
    # first remove anything in brackets, including spaces around
    # brackets
    s = re.sub(r' *\(.*?\) *', '', s)
    # strip a colon, anything following and any spaces before...
    s = re.sub(r' *:.*', '', s)    
    # next replace any numbers from 1 to 9
    rep = {'One': '1',
           'Two': '2',
           'Three': '3',
           'Four': '4',
           'Five': '5',
           'Six': '6',
           'Seven': '7',
           'Eight': '8',
           'Nine': '9'}
    for r in rep:
        s = s.replace(r, rep[r])
        s = s.replace(r.lower(), rep[r])
    return s

def MatchRugbyUnion(BDAQMarkets, BFMarkets):
    """Reurn list of tuples (m1,m2) where m1 and m2 are the matching
    markets"""
    # conversion from bdaq to bf market names; keys are bdaq market
    # names
    mname = {'Win Market': ['Outright Winner'],
             'Match Odds': ['Match Odds'],
             'Half-Time/Full-Time': ['Half-Time/Full-Time'],
             'First Scoring Play': ['First Scoring Play']
             }
    matches = []
    for m1 in BDAQMarkets:
        sp1 = m1.name.split('|')
        for m2 in BFMarkets:
            sp2 = m2.name.split('|')
            if sp2[-1] in mname.get(sp1[-1],[]):
                # go to level up
                if (level2convert(sp1[-2]) == sp2[-2]):
                    matches.append((m1,m2))
                    break
    if const.DEBUG:
        print "Matched %d/%d BDAQ markets" %(len(matches), len(BDAQMarkets))
        print "Markets not matched:"
        nomatch = [m.name for m in BDAQMarkets if not m
                   in [a[0] for a in matches]]
        print '\n'.join(nomatch)
    return matches

if __name__ == '__main__':
    dbman = database.DBMaster()

    # test matching of rugby union markets
    BDAQMarkets = dbman.ReturnMarkets('SELECT * FROM markets where exchange_id=? and market_name LIKE ?', (const.BDAQID,'|Rugby Union%'))
    BFMarkets =  dbman.ReturnMarkets('SELECT * FROM markets where exchange_id=? and market_name LIKE ?', (const.BFID,'|Rugby Union%'))

    matches = MatchRugbyUnion(BDAQMarkets, BFMarkets)


