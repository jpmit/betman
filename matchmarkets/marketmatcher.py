# marketmatcher.py
# James Mithen
# jamesmithen@gmail.com
#
# Functionality for finding pairs of matching markets, i.e. the same
# market on BDAQ and BF

from betman import const, database
from matchconst import EVENTMAP
import matchformula1
import matchrugbyunion
import matchsoccer

class MatchError(Exception): pass

# functions for matching two markets from the same event
# the event key used here is the BDAQ one
_MATCHFNS = {'Formula 1': matchformula1.MatchFormula1,
            'Rugby Union': matchrugbyunion.MatchRugbyUnion,
            'Soccer' : matchsoccer.MatchSoccer
            }

def _matchevent(m1s, m2s, eventname):
    """Call appropriate function to match markets m1s and m2s,
    as determined by the name"""
    if eventname not in _MATCHFNS:
        raise MatchError, "don't know how to match {0}"\
              .format(eventname)
    # this will return a list of tuples (m1,m2) where m1 and m2 are
    # the matching markets.
    return _MATCHFNS[eventname](m1s, m2s)

def GetMatchMarkets(m1s, m2s):
    """Get matching markets.
    m1s are BDAQ markets
    m2s are BF markets."""
    matchms = []
    # we need to go match m1s and m2s by event types
    # first get all event names for markets in m1s
    # converting to set is a trick to give unique elements,
    # then back to list again to sort
    m1names = list(set([m.eventname for m in m1s]))
    m1names.sort()
    matchms = []
    for name in m1names:
        bdaqms = [m for m in m1s if m.eventname == name]
        bfms = [m for m in m2s if m.eventname == EVENTMAP[name]]
        matchms += (_matchevent(bdaqms, bfms, name))
    # write matching markets to DB
    if const.WRITEDB:
        database.DBMaster().WriteMarketMatches(matchms)
    
    return matchms

def _matchselection(sel, sellist):
    """Return selection in sellist that 'matches' sel, or None if
    no match found"""
    # some of the BF names have trailing spaces, e.g. 'Sebastian
    # Vettel '.  This is clearly a bit cheeky.  Lets strip any
    # whitespace at start and end of name, and for both exchanges.
    selname = sel.name.strip()
    #print selname
    for s in sellist:
        if s.name.strip() == selname:
            return s
    return None

def GetMatchSelections(m1sels, m2sels):
    """Get matching selections.
    sel1s are BDAQ markets
    sel2s are BF markets.
    """
    # sel1s and sel2s should be [[s1,s2,s3m...],[s1,s2,s3,...]]
    # i.e. a list of lists, where each sub list is a list of selection
    # objects corresponding to a particular market
    assert (len(m1sels) == len(m2sels))
    matchsels = []
    # simple selection matching: if the names of the selection are the
    # same for both BDAQ and BF, they are probably the same
    # selection...
    for (sel1list,sel2list) in zip(m1sels, m2sels):
        # match the selections for this market: go through each bdaq
        # selection in turn and try to find a matching BF selection.
        for sel in sel1list:
            matchsel = _matchselection(sel, sel2list)
            if matchsel:
                # a matching selection was found
                matchsels.append((sel, matchsel))
    # write matching selections to DB
    if const.WRITEDB:
        database.DBMaster().WriteSelectionMatches(matchsels)

    return matchsels
