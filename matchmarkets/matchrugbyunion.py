# matchmarkets.py
# 18th July 2013
# Try to match markets between BF and BDAQ (!)

from betman import database, const
import numpy as np
import re

# hard coded mappings between BDAQ and BF.  Key is BDAQ name, value if BF name
_HARDCODED = {#'The Rugby Championship : Outright', 
              'Heineken Cup : Outright' : 'Heineken Cup 2013/14',
              'Aviva Premiership : Outright' : 'Aviva Premiership 2013/14',
              'RBS Six Nations 2014 : Outright' : 'RBS 6 Nations 2014',
              'RaboDirect Pro 12 : Grand Final Winner' : 'RaboDirect 2013/14'}

def level2convert(s):
    # any hardcoded names at this level
    if s in _HARDCODED:
        return _HARDCODED[s]

    # first remove anything in brackets, including spaces around
    # brackets
    s = re.sub(r' *\(.*?\) *', '', s)
    # remove any times
    s = re.sub(r'[0-9][0-9]:[0-9][0-9]\s', '', s)

    return s

def MatchRugbyUnion(BDAQMarkets, BFMarkets):
    """Reurn list of tuples (m1,m2) where m1 and m2 are the matching
    markets"""
    # conversion from bdaq to bf market names; keys are bdaq market
    # names
    mname = {'Win Market': ['Outright Winner','Grand Final Winner'],
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
                #print level2convert(sp1[-2]), sp2[-2]
                if (level2convert(sp1[-2]) == sp2[-2]):
                    matches.append((m1,m2))
                    break
    return matches

if __name__ == '__main__':
    dbman = database.DBMaster()

    # test matching of rugby union markets
    BDAQMarkets = dbman.ReturnMarkets('SELECT * FROM markets where exchange_id=? and market_name LIKE ?', (const.BDAQID,'|Rugby Union%'))
    BFMarkets =  dbman.ReturnMarkets('SELECT * FROM markets where exchange_id=? and market_name LIKE ?', (const.BFID,'|Rugby Union%'))

    matches = MatchRugbyUnion(BDAQMarkets, BFMarkets)


