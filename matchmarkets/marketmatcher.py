# marketmatcher.py

import matchformula1
import matchrugbyunion
import matchsoccer

class MatchError(Exception): pass

matchfns = {'Formula 1': matchformula1.MatchFormula1,
            'Rugby Union': matchrugbyunion.MatchRugbyUnion,
            'Soccer' : matchsoccer.MatchSoccer
            }

def match(m1s, m2s, name):
    """Call appropriate function to match markets m1s and m2s"""
    if name not in matchfns:
        raise MatchError, "don't know how to match %s" %name
    # this will return a list of tuples (m1,m2) where m1 and m2 are
    # the matching markets.
    return matchfns[name](m1s, m2s)
