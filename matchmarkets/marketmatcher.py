# marketmatcher.py
# James Mithen
# jamesmithen@gmail.com

"""
Functionality for finding pairs of matching markets, i.e. the same
market on BDAQ and BF.
"""

from betman import const, database, betlog
from betman.all.betexception import MatchError
from matchconst import EVENTMAP
import matchformula1
import matchrugbyunion
import matchsoccer
import matchhorse
import re

# functions for matching two markets from the same event. The event
# key used here is the BDAQ one.
_MATCHFNS = {'Formula 1':    matchformula1.match_formula1,
             'Rugby Union':  matchrugbyunion.match_rugbyunion,
             'Soccer' :      matchsoccer.match_soccer,
             'Horse Racing': matchhorse.match_horse
            }

def _matchevent(m1s, m2s, eventname):
    """
    Call appropriate function to match markets m1s and m2s, as
    determined by the name of the event.
    """

    if eventname not in _MATCHFNS:
        raise MatchError, "don't know how to match {0}"\
              .format(eventname)
    
    # this will return a list of tuples (m1,m2) where m1 and m2 are
    # the matching markets.
    return _MATCHFNS[eventname](m1s, m2s)

def get_match_markets(m1s, m2s):
    """
    Get matching markets.
    m1s are BDAQ markets
    m2s are BF markets.
    """

    matchms = []
    # we need to go match m1s and m2s by event types
    # first get all event names for markets in m1s
    # converting to set is a trick to give unique elements,
    # then back to list again to sort
    m1names = list(set([m.eventname for m in m1s]))
    m1names.sort()
    matchms = []
    # match markets for each event in turn
    for name in m1names:
        bdaqms = [m for m in m1s if m.eventname == name]
        bfms = [m for m in m2s if m.eventname == EVENTMAP[name]]
        matchms += (_matchevent(bdaqms, bfms, name))

        # write the markets not matched to log
        nomatch = [m.name for m in bdaqms if not m
                   in [a[0] for a in matchms]]
        betlog.betlog.debug("Matched {0}/{1} BDAQ {2} markets"\
                            .format(len(matchms), len(bdaqms),
                                    name))
        nmstr = '\n'.join(nomatch)
        betlog.betlog.debug("Markets not matched:\n{0}"\
                            .format(nmstr))
        
    # write matching markets to DB
    if const.WRITEDB:
        database.DBMaster().WriteMarketMatches(matchms)
    
    return matchms

def _matchselection(sel, sellist):
    """
    Return selection in sellist that 'matches' sel, or None if no
    match found.

    Here sel is a BDAQ selection names, and sellist is a list of BF
    selections.
    """
    
    # Horse Racing: the BDAQ horse racing selections have numbers in
    # them, but the BF ones dont', so lets remove the numbers from the
    # BDAQ selections.
    selname = ''.join(i for i in sel.name if not i.isdigit())

    # Soccer: the BDAQ draw selection is called 'Draw', but the
    # corresponding BF selection is 'The Draw', so let's rename the
    # BDAQ selection 'Draw'.
    if selname == 'Draw':
        selname = 'The Draw'

    # Remove any apostrophes from the BDAQ selection name.
    selname = selname.replace('\'','')
    
    # some of the BF names have trailing spaces, e.g. 'Sebastian
    # Vettel'.  This is clearly a bit cheeky.  Lets strip any
    # whitespace at start and end of name, and for both exchanges just
    # in case.
    selname = selname.strip().lower()

    for s in sellist:
        if s.name.strip().lower() == selname:
            return s

    # if we haven't matched here, try removing numbers with dot from
    # the BF selection name.  This is for matching horse racing
    # selections on US markets which look like '7. mazzy'
    for s in sellist:
        mat = re.match('\d+', s.name)
        if mat:
            sn = s.name[mat.end() + 2:]
        if sn.strip().lower() == selname:
            return s

    # we tried everything, so give up
    return None

def get_match_selections(m1sels, m2sels):
    """
    Get matching selections.
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
    for (sel1list, sel2list) in zip(m1sels, m2sels):
        # match the selections for this market: go through each bdaq
        # selection in turn and try to find a matching BF selection.
        for sel in sel1list:
            matchsel = _matchselection(sel, sel2list)
            if matchsel:
                # a matching selection was found
                matchsels.append((sel, matchsel))
            else:
                betlog.betlog.info(('No match found for BDAQ selection '
                                    '{0}').format(sel))
                
    # write matching selections to DB
    if const.WRITEDB:
        database.DBMaster().WriteSelectionMatches(matchsels)

    return matchsels
