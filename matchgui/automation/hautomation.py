import models
from automation import Automation
import datetime
from betman.strategy.bothmmstrategy import BothMMStrategy
from betman.strategy.mmstrategy import MMStrategy
import managers
import wx

# note class must be named MyAutomation for GUI loader
class MyAutomation(Automation):
    """Automation for horse racing.

    This will do market making on both BF and BDAQ, for ALL horse
    races during the pre-race period, from STARTTmins to ENDTmins
    before the race starts (we use STARTT minutes as a buffer as we
    don't want to place any 'in running' bets).

    """

    STARTT  = 16 # time in minutes before race start that we will
                 # begin market marking.
    ENDT    = 2  # time in minutes before race start to finish market
                 # making.
    MAXLAY  = 8  # only make markets on selections with lay price <
                 # this number at the time which they are added
                 # (STARTT mins before the race start).
    MAXBACK = 8  # same but for back, this means we won't make markets
                 # when there are no backers yet.

    UFREQ   = 2  # update frequency in ticks of strategies added.

    # when adding a market, should we use the API to get matching
    # selections? If False, we will simply query the DB.
    REFRESH_SELECTIONS = False

    def __init__(self):
        super(MyAutomation, self).__init__('Horse MM Automation')
        
        # we access data on markets and selections through the 'models'
        self.mmarkmodel = models.MatchMarketsModel.Instance()
        self.mselmodel = models.MatchSelectionsModel.Instance()

        # store time deltas for figuring out when strategies start/end
        self.starttdelta = datetime.timedelta(minutes=self.STARTT)
        self.endtdelta = datetime.timedelta(minutes=self.ENDT)

        # get all matching horse racing events from DB
        self.hmatches = self.get_all_markets()
        
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

    def get_all_markets(self):

        # get all matching horse racing events
        allhmatches = self.mmarkmodel.GetMatches('Horse Racing')

        curtime = datetime.datetime.now()

        # restrict to all horse races happening at least ENDT mins
        # in the future.
        hmatches = []
        for hmatch in allhmatches:
            # zeroth item is BDAQ market (but both should work since
            # they should have the same start time).
            if (curtime + self.endtdelta < hmatch[0].starttime):
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

        # remove strategies with < ENDT mins to go until start time.
        strats_finished = []
        for i, (s, m) in enumerate(self._strategies):
            if (curtime + self.endtdelta > m.starttime):
                # remove strategy from app/engine
                self.remove_strategy(engine, s)
                # remove from internal 
                strats_finished.append(i)
        strats_finished.reverse()
        for i in strats_finished:
            self._strategies.pop(i)

        # add strategies with < STARTT mins to go until start time.
        strats_seen = []
        for (i, hmatch) in enumerate(self.hmatches):
            if (curtime + self.starttdelta > hmatch[0].starttime):
                # add the strategies for this market pair
                print 'adding strategies for', hmatch
                self.add_strategy(engine, hmatch)
                # remove from remaining matches list
                strats_seen.append(i)
        strats_seen.reverse()
        for i in strats_seen:
            self.hmatches.pop(i)

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

        # warning, this could fail if we are adding many strategies at
        # once (calling this function multiple times in close
        # succession), since we call BDAQ and BF api once for each
        # pair of mids.  if so, try refresh = False, although then
        # beware since we will use 'stale' data.
        bdaqsels, bfsels = self.mselmodel.\
                           GetMatchingSels(hmatch[0].id, hmatch[1].id, refresh=True)

        # we want to add market making strategy on both exchanges, for
        # all selections that have prices < some certain number (we
        # don't want to make markets on horses whose odds are, say
        # 120, as this is too risky.
        for (s1, s2) in zip(bdaqsels, bfsels):
            # only add strategies for which are within our limits on
            # both BDAQ (and maybe also BF).
            if ((s1.best_lay() < self.MAXLAY) and (s1.best_back() < self.MAXBACK)):
                #and (s2.best_lay() < self.MAXLAY) and (s2.best_back() < self.MAXBACK)):
                # debug
                print s1.name, 'best lay', s1.best_lay(), s1.name, 'best back', s1.best_back()
                # BDAQ only at the moment due to problem with multithreaded BF betting.
                strat = MMStrategy(s1)#BothMMStrategy(s1, s2)
                # set update frequency 
                setattr(strat, managers.UTICK, self.UFREQ)
                
                if self.app:
                    self.app.AddStrategy('Make Both', s1.name, strat, s1, s2)
                else:
                    engine.add_strategy(strat)

                # add to internal bookkeeping, note second element of
                # tuple is the bdaq market, not the selection (since
                # the market has the starttime property).
                self._strategies.append((strat, hmatch[0]))
