from automation import Automation
import datetime
from betman.strategy.bothmmstrategy import BothMMStrategy
from betman.strategy.mmstrategy import MMStrategy
from betman.core import managers, stores
from betman.core.stores import updaters
from betman.all.betexception import InternalError
import wx

# note class must be named MyAutomation for GUI loader
class MyAutomation(Automation):
    """Automation for horse racing.

    This will do market making on both BF and BDAQ, for ALL horse
    races during the pre-race period, from STARTTmins to ENDTmins
    before the race starts (we use STARTT minutes as a buffer as we
    don't want to place any 'in running' bets).

    """

    # TODO(?): at some point, all of the hard coded parameters below
    # could be selected via the GUI.

    _STARTT  = 30 # time in minutes before race start that we will
                  # begin market marking.
    _ENDT    = 2  # time in minutes before race start to finish market
                  # making.
    _MAXLAY  = 8  # only make markets on selections with lay price <
                  # this number at the time which they are added
                  # (STARTT mins before the race start).
    _MAXBACK = 8  # same but for back, this means we won't make markets
                  # when there are no backers yet.

    _UFREQ   = 2  # update frequency in ticks of strategies added.

    _EXCHANGE = 'BF' # BF, BDAQ or BOTH

    _COUNTRIES = 'UKIRE' # currently can be either UKIRE or ALL

    _STRATNAME = {'BF': 'Make BF', # mapping from _EXCHANGE to GUI name.
                  'BDAQ': 'Make BDAQ',
                  'BOTH': 'Make Both'}

    # when adding a market, should we use the API to get matching
    # selections? If False, we will simply query the DB.
    _REFRESH_SELECTIONS = False

    def __init__(self):
        super(MyAutomation, self).__init__('Horse MM Automation')
        
        # we access data on markets and selections through the 'stores'
        self._mstore = stores.MatchMarketStore.Instance()
        self._sstore = stores.MatchSelectionStore.Instance()
        self._supdater = updaters.MatchSelectionUpdater.Instance()

        # store time deltas for figuring out when strategies start/end
        self._starttdelta = datetime.timedelta(minutes=self._STARTT)
        self._endtdelta = datetime.timedelta(minutes=self._ENDT)

        # get all matching horse racing events; this will filter out
        # those we aren't interested in
        self._hmatches = self.get_all_markets()

        # print all markets
        if self._hmatches:
            print 'Automation has markets:'
            for hm in self._hmatches:
                # this is the bdaq name
                print hm[0].name
        
        # we keep an internal count of the strategies we have added
        # that are currently running. This means when updating the
        # global stratgroup, we only add and remove those that we are
        # responsible for (we don't touch other strategies that could
        # have been added via other automations/the GUI.
        # self.strategies is list of tuples (strategy_object,
        # bdaqmark).
        self._strategies = []

        # slightly hacky for now: see if we are running the GUI and
        # store a reference to it.  This is so that when we add or
        # remove strategies we can also do this for the actual app.
        try:
            self.app = wx.GetApp()
        except:
            self.app = None

    def filter_market_country(self, bdaqmark):
        """Return True if the market country is ok, False otherwise."""

        if self._COUNTRIES == 'UKIRE':
            nm = bdaqmark.name.split('|')[2]
            if (nm == 'UK Racing') or (nm == 'Irish Racing'):
                return True
            else:
                return False
        elif self._COUNTRIES == 'ALL':
            return True
        else:
            raise InternalError, 'countries must be \'UKIRE\' or \'ALL\''

    def get_all_markets(self):

        # get all matching horse racing events
        allhmatches = self._mstore.get_matches('Horse Racing')

        curtime = datetime.datetime.now()

        # restrict to all horse races happening at least ENDT mins in
        # the future, and use _COUNTRIES to filter out some races.
        hmatches = []
        for hmatch in allhmatches:
            bdaqmark = hmatch[0]
            if self.filter_market_country(bdaqmark):
                if (curtime + self._endtdelta < bdaqmark.starttime):
                    hmatches.append(hmatch)

        # list of tuples (m1, m2) where m1 is BDAQ market and m2 is BF
        # market.
        return hmatches

    def update(self, engine):
        """Add/remove strategies from the stratgroup.

        We add strategy when the time first passes starttime - STARTT.
        We remove a strategy when the time first passes starttime -
        ENDT.

        TODO: do we really want to call this every tick?  Probably
        better every minute since we won't be adding/removing
        strategies all that often. EDIT: now calling this every minute
        only (although it wont happen 'on the minute').

        """

        curtime = datetime.datetime.now()

        # remove strategies with < _ENDT mins to go until start time.
        strats_finished = []
        for i, (s, m) in enumerate(self._strategies):
            # time left to live in seconds
            ttl = (m.starttime - curtime - self._endtdelta).total_seconds()

            if (ttl < 0):
                # remove strategy from app/engine
                self.remove_strategy(engine, s)
                # remove from internal 
                strats_finished.append(i)
            else:
                # send a pulse to the strategy so that it knows time
                # left
                s.update_ttl(ttl)

        strats_finished.reverse()
        for i in strats_finished:
            self._strategies.pop(i)

        # add strategies with < STARTT mins to go until start time.
        strats_seen = []
        for (i, hmatch) in enumerate(self._hmatches):
            if (curtime + self._starttdelta > hmatch[0].starttime):
                # add the strategies for this market pair
                print 'adding strategies for', hmatch
                self.add_strategy(engine, hmatch)
                # remove from remaining matches list
                strats_seen.append(i)
        strats_seen.reverse()
        for i in strats_seen:
            self._hmatches.pop(i)

    def remove_strategy(self, engine, s):
        """Remove strategy s."""

        if self.app:
            # GUI is running
            self.app.RemoveStrategyByObject(s)
        else:
            # remove directly from engine
            engine.remove_strategy(s)
    
    def add_strategy(self, engine, hmatch):
        """Add the strategies we want for hmatch = (m1, m2).

        (m1, m2) are the matching markets.  This routine adds
        strategies for a single pair of matching markets only.

        """
        
        bdaqmid = hmatch[0].id
        
        # force update of selection information for the matching
        # market.
        self._supdater.update_selection_information(bdaqmid)

        bdaqsels, bfsels = self._sstore.\
                           get_matching_selections(bdaqmid)

        # we want to add market making strategy on both exchanges, for
        # all selections that have prices < some certain number (we
        # don't want to make markets on horses whose odds are, say
        # 120, as this is too risky.
        for (s1, s2) in zip(bdaqsels, bfsels):
            if (self._EXCHANGE == 'BDAQ'):
                sbet = s1
            elif (self._EXCHANGE == 'BF'):
                sbet = s2
            else:
                raise InternalError, '_EXCHANGE must be either BDAQ or BF'
                
            # only add strategies for which are within our limits
            if ((sbet.best_lay() < self._MAXLAY) and (sbet.best_back() < self._MAXBACK)):
                # debug
                print sbet.name, 'best lay', sbet.best_lay(), sbet.name, 'best back', sbet.best_back()
                strat = MMStrategy(sbet, auto=True)
                # set update frequency 
                setattr(strat, managers.UTICK, self._UFREQ)
                
                if self.app:
                    self.app.AddStrategy(self._STRATNAME[self._EXCHANGE], 
                                         s1.name, strat, s1, s2)
                else:
                    engine.add_strategy(strat)

                # add to internal bookkeeping, note second element of
                # tuple is the bdaq market, not the selection (since
                # the market has the starttime property).
                self._strategies.append((strat, hmatch[0]))
