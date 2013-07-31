# marketmatcher.py
# James Mithen
# jamesmithen@gmail.com
#
# Functionality for finding pairs of matching markets, i.e. the same
# market on BDAQ and BF

from betman import const, database
import matchformula1
import matchrugbyunion
import matchsoccer

class MatchError(Exception): pass

# mapping from BDAQ event names to BF event names. most of the event
# names are the same but some are different!
# note that the following BF events don't have BDAQ equivalents at the
# moment:
# Athletics
# Basketball
# Bowls
# Financial Bets
# Netball
# Poker
# Politics

EVENTMAP = {'American Football' : 'American Football',
            'Australian Rules'  : 'Australian Rules', 
            'Baseball'          : 'Baseball',         
            'Boxing'            : 'Boxing',           
            'Cricket'           : 'Cricket',          
            'Cycling'           : 'Cycling',          
            'Darts'             : 'Darts',            
            'Formula 1'         : 'Motor Sport',
            'GAA' 				  : 'Gaelic Games',
            'Golf'              : 'Golf',             
            'Greyhound Racing'  : 'Greyhound Racing', 
            'Horse Racing'      : 'Horse Racing',     
            'Mixed Martial Arts': 'Mixed Martial Arts',
            'Rugby League'      : 'Rugby League',       
            'Rugby Union'       : 'Rugby Union',        
            'Soccer'            : 'Soccer',             
            'Special Bets'      : 'Special Bets',       
            'Tennis'            : 'Tennis'             
}

# functions for matching two markets from the same event
# the event key used here is the BDAQ one
MATCHFNS = {'Formula 1': matchformula1.MatchFormula1,
            'Rugby Union': matchrugbyunion.MatchRugbyUnion,
            'Soccer' : matchsoccer.MatchSoccer
            }

def matchevent(m1s, m2s, eventname):
    """Call appropriate function to match markets m1s and m2s,
    as determined by the name"""
    if eventname not in MATCHFNS:
        raise MatchError, "don't know how to match {0}".format(eventname)
    # this will return a list of tuples (m1,m2) where m1 and m2 are
    # the matching markets.
    return MATCHFNS[eventname](m1s, m2s)

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
        matchms += (matchevent(bdaqms, bfms, name))
    # write matching markets to DB
    if const.WRITEDB:
        database.DBMaster().WriteMarketMatches(matchms)
    
    return matchms
