# matchsoccer.py
# James Mithen
# jamesmithen@gmail.com

from betman import database, const, betlog
import numpy as np
import re

def bdaqconvert(s):
    # first remove anything in brackets, including spaces around
    # brackets
    s = re.sub(r' *\(.*?\) *', '', s)
    # strip any times like 19:30 out as well as trailing spaces
    s = re.sub(r'[0-9][0-9]:[0-9][0-9] *', '', s)    
    # strip a colon, anything following and any spaces before...
    s = re.sub(r' *:.*', '', s)
    # remove 'The - matches the championship
    s = s.replace('The ','')
    # english leagues 1, 2
    s = s.replace('English League One','League 1')
    s = s.replace('English League Two','League 2')
    # bundesliga
    s = s.replace('Bundesliga','Bundesliga 1')
    # spain
    s = s.replace('La Liga 2013/2014','Primera Division')
    # remove city for stoke, hull etc..
    s = s.replace('Hull City','Hull')
    s = s.replace('Stoke City','Stoke')
    s = s.replace('Bayern Munich','B Munich')
    # remove any leading or trailing spaces
    #s = s.strip()
    #print s
    return s

def bfconvert(s):
    # remove barclays for english premier league
    s = s.replace('Barclays ','')
    # replace airtricity with irish for irish premier league
    s = s.replace('Airtricity','Irish')
    return s

def match_soccer(BDAQMarkets, BFMarkets):
    """
    Return list of tuples (m1,m2) where m1 and m2 are the matching
    markets.
    """
    
    # conversion from bdaq to bf market names; keys are bdaq market
    # names
    mname = {'Win Market': ['Winner', 'Winner 2013/14',
                            'Winner 2013', 'Winner 2014'],
             'Match Odds': ['Match Odds'],
             'Half-Time/Full-Time': ['Half-Time/Full-Time'],
             'First Scoring Play': ['First Scoring Play'],
             'Top 4 Finish': ['Top 4 Finish','Top 4 Finish 2013/2014']
             }
    matches = []
    for m1 in BDAQMarkets:
        sp1 = m1.name.split('|')
        n1 = bdaqconvert(sp1[-2])
        for m2 in BFMarkets:
            sp2 = m2.name.split('|')
            if sp2[-1] in mname.get(sp1[-1],[]):
                # go to level up
                n2 = bfconvert(sp2[-2])
                if (n1 == n2):
                    matches.append((m1,m2))
                    break
    return matches
