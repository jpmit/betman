"""All other stores except for OrderStore and Pricing Store.

At present we have a MatchMarketStore, which stores details of the
markets for both BDAQ and BF (including mapping between mids), and a
MatchSelectionStore, which does the same for selections.  The
MatchSelectionStore stores the selections in the BDAQ display order,
so is useful for the GUI.

"""

import datetime
from operator import itemgetter

from betman import const, database
from betman.all.singleton import Singleton
from betman.matching.matchconst import EVENTMAP

@Singleton
class MatchMarketStore(object):

    """Map markets between the exchanges."""
    
    # if True, we will initialise the the store with information in
    # the sqlite database.
    INITDB = True
    
    def __init__(self):

        # key to match_cache is event name, value is list of tuples
        # (m1, m2) where m1 and m2 are the matching markets (m1 is the
        # BDAQ market, m2 is the BF market.  The ordering of the
        # tuples is the same as the ordering that appears in the GUI.
        self._match_cache = {}

        # store a dict that maps BDAQ mids to BF mids
        self._BDAQmap_cache = {}

        # and a dict that maps BF mids to BDAQ mids
        self._BFmap_cache = {}

        # and a dict that maps BDAQ mids to their market objects
        self._BDAQ_cache = {}

        # and a dict that maps BF mids to their market objects
        self._BF_cache = {}

        # singleton that controls DB access
        self._dbman = database.DBMaster()

        if self.INITDB:
            self.init_caches_from_DB()
        else:
            self.init_caches_empty()

    def init_caches_from_DB(self):
        """Initialise matching markets cache from the database."""

        for ename in EVENTMAP:
            mmarks = self._dbman.return_market_matches([ename])
            self.set_caches(ename, mmarks)

    def init_caches_empty(self):
        """Initialise the matching markets cache as empty."""
        
        for ename in EVENTMAP:
            self._match_cache[ename] = []
            # the other caches are set to be empty after __init__

    def get_BFmid_from_BDAQmid(self, bdaqmid):
        return self._BDAQmap_cache[bdaqmid]

    def get_BDAQmid_from_BFmid(self, bfmid):
        return self._BFmap_cache[bfmid]

    def get_market_name(self, exid, mid):
        if (exid == const.BDAQID):
            return self.get_name_from_BDAQmid(mid)
        elif (exid == const.BFID):
            return self.get_name_from_BFmid(mid)            
        else:
            return ''

    def get_BDAQname_from_mid(self, exid, mid):
        if (exid == const.BFID):
            mid = self.get_BDAQmid_from_BFmid(mid)
        return self.get_name_from_BDAQmid(mid)

    def get_name_from_BDAQmid(self, bdaqmid):
        return self._BDAQ_cache[bdaqmid].name

    def get_name_from_BFmid(self, bfmid):
        return self._BF_cache[bfmid].name

    def set_caches(self, ename, mmarks):
        """Called if initialising from DB."""

        # ordered list of matching markets for event ename
        self._match_cache[ename] = mmarks

        for m1, m2 in mmarks:
            m1id = m1.id
            m2id = m2.id
            # map bdaq mid to bf mid
            self._BDAQmap_cache[m1id] = m2id

            # map bf mid to bdaq mid
            self._BFmap_cache[m2id] = m1id

            # map bdaq mid to market object
            self._BDAQ_cache[m1id] = m1

            # map bf mid to market object
            self._BF_cache[m2id] = m2

    def add_matching_markets(self, ename, mmarks):
        """Refresh the store of matching markets for a particular event.  

        Note that at the moment this replaces any existing matching
        markets stored for the event i.e. we simply overwrite the
        cache for ename with mmarks.

        ename  - name of event e.g. 'Horse Racing'.
        mmarks - list of tuples (m1, m2) where m1 is a BDAQ market
                 that matches the BF market m2.

        """

        self.set_caches(ename, mmarks)

        # write to the matching markets table of the DB
        self._dbman.write_market_matches(mmarks)

        # write each individual market to the market table of the DB
        allmarks = [itemgetter(j)(i) for j in [0,1] for i in mmarks]
        self._dbman.write_markets(allmarks, datetime.datetime.now())

    def get_matches(self, ename):
        """Return list of matching market tuples for a particular event."""

        return self._match_cache[ename]

@Singleton
class MatchSelectionStore(object):

    """Map selections between the exchanges."""

    # if True, init the selection store with information in the DB.
    # Note: we probably don't want to do this, or at least we should
    # filter out most of the matching selections, since otherwise
    # we'll be storing a lot of information about selections from
    # markets that ended long ago.
    INITDB = True
    
    def __init__(self):

        # matching selections keys are bdaqmid, values are
        # [(bdaq_sels, bf_sels)] where bdaq_sels and bf_sels are lists
        # of bdaq and bf selections, ordered as displayed on the BDAQ
        # website.  Instead of dumping everything from the DB into the
        # cache immediately, we add to the cache 'as needed'.
        self._match_cache = {}

        # map a BF sid to a BDAQ sid; note this has an additional
        # layer compared to the BDAQ cache since we must store the
        # market id.
        self._BFmap_cache = {}

        # map a BDAQ sid to selection object.  Note: we do not have an
        # equivalent cache for BF sid's since these do not map
        # uniquely onto selections (an annoying feature of the BF
        # API).  That is, we need both the BF mid and sid to map to a
        # BDAQ sid.
        self._BDAQ_cache = {}

        # we need to access the market store since when we add
        # matching selections, we need to find the BF mid that matches
        # the given BDAQ mid.
        self._mstore = MatchMarketStore.Instance()

        # singleton that controls DB access
        self._dbman = database.DBMaster()

        if self.INITDB:
            self.init_caches_from_DB()

    def init_caches_from_DB(self):
        bdaqsels, bfsels = self._dbman.return_selection_matches()
        m_cache = {}
        for (s1, s2) in zip(bdaqsels, bfsels):
            bdaqmid = s1.mid
            bfmid = s2.mid
            
            # match cache: slightly horrible, we fill this up here,
            # but later we need to re-order the selections according
            # to their display order.
            if bdaqmid in self._match_cache:
                self._match_cache[bdaqmid][0].append(s1)
                self._match_cache[bdaqmid][1].append(s2)                
            else:
                # tuple of two lists bdaqsels, bfsels
                self._match_cache[bdaqmid] = ([s1], [s2])

            # mapping from BF sid (for this mid) to BDAQ sid
            if bfmid in self._BFmap_cache:
                self._BFmap_cache[bfmid][s2.id] = s1.id
            else:
                self._BFmap_cache[bfmid] = {s2.id: s1.id}

            # mapping from BDAQ sid to selection object
            self._BDAQ_cache[s1.id] = s1

        # sort self._match_cache so we have two lists of selections
        # sorted by the BDAQ display order.
        mykey = lambda k: k[1].dorder
        for bdaqmid in self._match_cache:
            bdaqsels = self._match_cache[bdaqmid][0]
            bfsels = self._match_cache[bdaqmid][1]
            # note only BDAQ selections have a display order.
            indices, sbdaqsels = zip(*sorted(enumerate(bdaqsels), key=mykey))
            sbfsels = [bfsels[i] for i in indices]
            self._match_cache[bdaqmid] = (sbdaqsels, sbfsels)

    def add_matching_selections(self, bdaqmid, bdaqsels, bfsels):
        """Add matching selections.

        bdaqsels and bfsels should be sorted in the correct display
        order.

        """
        
        # add to match cache
        self._match_cache[bdaqmid] = (bdaqsels, bfsels)

        # get the BF mid from bdaq mid
        bfmid = self._mstore.get_BFmid_from_BDAQmid(bdaqmid)

        # bfmid will not be in the cache unless we got it from the
        # DB on initialization.
        if bfmid not in self._BFmap_cache:
            self._BFmap_cache[bfmid] = {}

        # mapping from BF sid (for this mid) to BDAQ sid
        for s1, s2 in zip(bdaqsels, bfsels):
            self._BFmap_cache[bfmid][s2.id] = s1.id

            # mapping from BDAQ sid to selection object
            self._BDAQ_cache[s1.id] = s1

        # write to the matching selections table of the DB
        self._dbman.write_selection_matches(zip(bdaqsels, bfsels))
        
        # write each individual selection to the selections table of the DB
        self._dbman.write_selections(bdaqsels + bfsels, datetime.datetime.now())

    def get_matching_selections(self, bdaqmid):
        """Return two lists bdaqsels, bfsels, of matching selections.

        bdaqsels[i] is the selection that matches bfsels[i], and the
        ordering of the selections is that given by the BDAQ display
        order.

        if we don't currently have have any, we will try to retreive
        it from the database.  If we don't have it in the database
        either, we will return two empty lists [], [].

        """

        if bdaqmid in self._match_cache:
            bdaqsels, bfsels = self._match_cache[bdaqmid]
        else:
            # try filling up the cache from the DB, will get empty
            # lists if not found.
            bdaqsels, bfsels = self._dbman.return_selection_matches([bdaqmid])

        # put entries into match cache.
        self._match_cache[bdaqmid] = (bdaqsels, bfsels)

        # and into map cache from BF sid to BDAQ sid, and cache from
        # BDAQ sid to selection object.
        seldict = {}
        for s1, s2 in zip(bdaqsels, bfsels):
            seldict[s2.id] = s1.id
            self._BDAQ_cache[s1.id] = s1

        # we need the BF mid here
        bfmid = self._mstore.get_BFmid_from_BDAQmid(bdaqmid)
        self._BFmap_cache[bfmid] = seldict

        return bdaqsels, bfsels

    def get_BDAQ_name(self, exid, mid, sid):
        """Return BDAQ name of selection."""

        if (exid == const.BFID):
            # map BF sid to BDAQ sid
            sid = self._BFmap_cache[mid][sid]
        return self._BDAQ_cache[sid].name
