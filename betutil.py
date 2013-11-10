# betutil.py
# James Mithen
# jamesmithen@gmail.com

"""Utility stuff for main betting program."""

import os
import pickle
from betman import const, database, betlog
from betman.strategy import strategy, cxstrategy

PICKPATH = os.path.join(os.path.split(const.MASTERDB)[0],
                        'stratgroup.pkl')
PKLPROT = 2

def save_strategies(bdaqids=[], instantonly = True):
    """
    Using info in the DB, get strategies and save these to pickle
    file.

    bdaqids - list of BDAQ market ids allowed.  If empty, all market
              ids are allowed.
    """

    sgroup = strategy.StrategyGroup()

    # add strategies here
    msels = database.DBMaster().ReturnSelectionMatches(bdaqids)

    if bdaqids:
        # filter out any strategies not involving one of the markets
        # listed in bdaqids
        for ms in list(msels):
            if ms[0].mid not in bdaqids:
                msels.remove(ms)

    # alter the prices so that we get instant opp!!
    #msels[0][0].backprices[0] = (1.50, 10)
    #msels[0][1].layprices[0] = (1.01, 10)        
    for m in msels:
        sgroup.add(cxstrategy.CXStrategy(m[0], m[1], instantonly))

    betlog.betlog.debug("Created {0} strategies from DB"\
                        .format(len(sgroup)))

    # pickle the strategy group - the main application will read this
    # pickle file.
    pickle_stratgroup(sgroup)
    return

def pickle_stratgroup(sgroup):
    """Pickle the StrategyGroup object."""
    
    of = open(PICKPATH, 'wb')
    pickle.dump(sgroup, of, protocol=PKLPROT)
    of.close()
    return

def unpickle_stratgroup():
    """Return StrategyGroup object from pickle file."""
    
    f = open(PICKPATH, 'rb')
    sgroup = pickle.load(f)
    f.close()

    # this initialises cursor object
    for s in sgroup.strategies:
        if hasattr(s, 'dbman'):
            s.dbman = database.DBMaster()
    
    return sgroup
