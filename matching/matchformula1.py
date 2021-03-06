# matchformula1.py
# James Mithen
# jamesmithen@gmail.com

from betman import database, const
import numpy as np

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

def match_formula1(BDAQMarkets, BFMarkets):
    """
    Return list of tuples (m1,m2) where m1 and m2 are the matching
    markets.
    """
    
    # For formula 1, we look straight at the 2nd level of BDAQ names,
    # that is, ignore 'Win Market etc'.  Next, we check that all of
    # the words in the second level name are identical to the words in
    # the top level name of the BF market name.  This means that e.g.
    # BDAQ name of |Formula 1|2013 Drivers Championship|Win Market
    # will match BF name of |Motor Sport|Formula 1 2013|Drivers
    # Championship 2013 .  note only 2 BDAQ markets in this category
    # at time of writing!
    matches = []
    for m1 in BDAQMarkets:
        sp1 = m1.name.split('|')
        name1 = sp1[-2]
        words1 = name1.split()
        for m2 in BFMarkets:
            sp2 = m2.name.split('|')
            name2 = sp2[-1]
            words2 = name2.split()
            # if all the words in name 1 and name 2 match (i.e., they
            # may be in a different order in each), then the markets
            # are the same.
            for (wnum, word) in enumerate(words1):
                if word not in words2:
                    # try next markets
                    break
                if wnum == len(words1) - 1:
                    matches.append((m1,m2))
    return matches
