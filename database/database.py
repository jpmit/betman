# database.py
# James Mithen
# jamesmithen@gmail.com
#
# Interface for interacting with database

import os
import sqlite3
from betman import const, Market, Selection, util, order
from betman.all.betexception import DBError, DBCorruptError
from betman.matchmarkets.matchconst import EVENTMAP
import schema

class DBMaster(object):
    """Simple interface to the main database"""

    # singleton design pattern
    _instance = None
    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(DBMaster, cls).__new__(cls, *args,
                                                         **kwargs)
        return cls._instance

    def __init__(self, create=False):
        self._isopen = False
        self.CreateIfNotExist()
        self.open()

    def CreateIfNotExist(self):
        """Create the database if it doesn't already exist"""
        if not os.path.exists(const.MASTERDB):
            self.CreateTables()

    def open(self):
        if not self._isopen:
            self.conn = sqlite3.connect(const.MASTERDB)
            self.cursor = self.conn.cursor()
            self._isopen = True

    def close(self):
        """Closing will unlock the database"""
        self.conn.close()
        self._isopen = False

    def WriteOrderMatches(self, omatches, tplaced):
        """Write to matchorders table"""
        # check database is open
        if not self._isopen:
            self.open()

        # insertion string
        qins = ('INSERT INTO {0} (order1_id, order2_id, tplaced) '
                'values (?,?,?)'.\
                format(schema.MATCHORDERS))
        alldata = [(o1.oref, o2.oref, tplaced) for (o1, o2) in omatches]        

        self.cursor.executemany(qins, alldata)
        self.conn.commit()

    def WriteSelectionMatches(self, selmatches):
        """Write to matchselections table"""
        # check database is open
        if not self._isopen:
            self.open()

        # insertion string
        qins = ('INSERT INTO {0} (ex1_mid, ex1_sid, ex1_name, ex2_mid, ex2_sid'
                ', ex2_name) values (?,?,?,?,?,?)'.\
                format(schema.MATCHSELS))
        
        for (s1,s2) in selmatches:
            data = (s1.mid, s1.id, s1.name, s2.mid, s2.id, s2.name)
            try:
                self.cursor.execute(qins, data)
            except sqlite3.IntegrityError:
                # already have matching market (hopefully this same
                # one!) in database
                pass
        self.conn.commit()

    def ReturnMarketMatches(self, elist=[]):
        """Return market matches.  If list of event names elist is not
        given, return all markets in marketmatches table.  If given,
        elist should be a list of BDAQ Event names."""
        # Note: there is definitely a much better way to accomplish
        # what is below using joins.  Once I actually know something
        # about SQL I shall come back to this.

        # check database is open
        if not self._isopen:
            self.open()
        
        # first query matchingmarkets 
        qstr = 'SELECT * FROM {0}'.format(schema.MATCHMARKS)
        qargs = ()
        if elist:
            # check here that all the entries in elist are valid BDAQ
            # event names
            for e in elist:
                if e not in EVENTMAP:
                    raise DBError, '{0} is not a valid event'.format(e)
            
            qargs = ['|'+elist[0]+'%']
            likestr = ' WHERE (ex1_name LIKE ?'
            # add the other events
            if len(elist) > 1:
                for ename in elist[1:]:
                    likestr = '{0} OR ex1_name LIKE ?'.format(likestr)
                    qargs.append('|'+ename+'%')
            likestr = likestr + ')'
            qstr = qstr + likestr
            qargs = tuple(qargs)

        # get the matching markets we want
        mm = self.cursor.execute(qstr, qargs).fetchall()
        # exchange 1 (BDAQ) mid is first value
        matchmarkets = []
        for m in mm:
            ex1mid = m[0]
            ex2mid = m[2]
            ex1mark = self.ReturnMarkets('SELECT * FROM {0} where '
                                         'exchange_id=? and market_id=?'\
                                         .format(schema.MARKETS),
                                         (const.BDAQID, ex1mid))
            ex2mark = self.ReturnMarkets('SELECT * FROM {0} where '
                                         'exchange_id=? and market_id=?'\
                                         .format(schema.MARKETS),
                                         (const.BFID, ex2mid))
            # check our queries worked.  If they didn't, then the
            # database is corrupted, since the market is listed in the
            # matching markets table but not in the markets table.
            for em, eid in zip([ex1mark, ex2mark], [ex1mid, ex2mid]):
                if not em:
                    raise DBCorruptError, ('market id {0} not found in '
                                           'table {1}'\
                                           .format(eid, schema.MARKETS))
                
            matchmarkets.append((ex1mark[0], ex2mark[0]))
        return matchmarkets

    def ReturnSelectionMatches(self, bdaqmids=[]):
        """
        Return selection matches for market ids in bdaqmids.  If
        bdaqmids not passed, return all selection matches.
        """
        # Note: there is definitely a much better way to accomplish
        # what is below using joins.  Once I actually know something
        # about SQL I shall come back to this.

        # check database is open
        if not self._isopen:
            self.open()
        
        # first query matching selection table
        qstr = 'SELECT * FROM {0}'.format(schema.MATCHSELS)

        if bdaqmids:
            # limit to certain markets
            if len(bdaqmids) == 1:
                qstr = '{0} WHERE ex1_mid=?'.\
                       format(qstr)
                qargs = (bdaqmids[0],)
            else:
                qstr = '{0} WHERE ex1_mid in ({1})'.\
                   format(qstr, ','.join(['?' for i in bdaqmids]))
                qargs = tuple(bdaqmids)
        else:
            qargs = ()

        # get the matching selections we want
        msels = self.cursor.execute(qstr, qargs).fetchall()
        matchsels = []
        for s in msels:
            ex1mid = s[0]
            ex1sid = s[1]
            ex2mid = s[3]
            ex2sid = s[4]
            ex1sel = self.ReturnSelections('SELECT * FROM {0} where '
                                           'exchange_id=? and market_id=? and selection_id=?'\
                                           .format(schema.SELECTIONS),
                                           (const.BDAQID, ex1mid, ex1sid))
            ex2sel = self.ReturnSelections('SELECT * FROM {0} where '
                                           'exchange_id=? and market_id=? and selection_id=?'\
                                           .format(schema.SELECTIONS),
                                           (const.BFID, ex2mid, ex2sid))
            # check our queries worked.  If they didn't, then the
            # database is corrupted, since the selection is listed in the
            # matching selections table but not in the markets table.
            for es, eid in zip([ex1sel, ex2sel], [ex1sid, ex2sid]):
                if not es:
                    raise DBCorruptError, ('selection id {0} not found in '
                                           'table {1}'\
                                           .format(eid, schema.SELECTIONS))
            
            matchsels.append((ex1sel[0], ex2sel[0]))
        return matchsels

    def WriteMarketMatches(self, matches):
        """Write to matchingmarkets table"""

        # check database is open
        if not self._isopen:
            self.open()

        # insertion string
        qins = ('INSERT INTO {0} (ex1_mid, ex1_name, ex2_mid'
                ', ex2_name) values (?,?,?,?)'.format(schema.\
                                                      MATCHMARKS))

        for m1,m2 in matches:
            data = (m1.id, m1.name, m2.id, m2.name)
            try:
                self.cursor.execute(qins, data)
            except sqlite3.IntegrityError:
                # already have matching market (hopefully this same
                # one!) in database
                pass
        self.conn.commit()

    def WriteSelections(self, selections, tstamp):
        """Write to selections table"""

        # check database is open
        if not self._isopen:
            self.open()
        
        # if a row doesn't exist with this exchange id and market id
        # we insert it, otherwise we update (since inrunning could have
        # changed).  This is probably not the most efficient way of
        # accomplishing that.
        qins = ('INSERT INTO {0} (exchange_id, market_id, '
                'selection_id, name, b_1, bvol_1, b_2, bvol_2, b_3, '
                'bvol_3, b_4, bvol_4, b_5, bvol_5, lay_1, lvol_1, '
                'lay_2, lvol_2, lay_3, lvol_3, lay_4, lvol_4, '
                'lay_5, lvol_5, src, wsn, last_checked) values '
                '(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,'
                ' ?, ?, ?, ?, ?, ?, ?, ?, ?)')
        qupd = ('UPDATE {0} SET b_1=?, bvol_1=?, b_2=?, bvol_2=?, '
                'b_3=?, bvol_3=?, b_4=?, bvol_4=?, b_5=?, bvol_5=?, '
                'lay_1=?, lvol_1=?, lay_2=?, lvol_2=?, lay_3=?, lvol_3=?, '
                'lay_4=?, lvol_4=?, lay_5=?, lvol_5=?, src=?, wsn=?, last_checked=? '
                'WHERE exchange_id=? and market_id=? and selection_id=?'\
                .format(schema.SELECTIONS))

        # all the data to insert
        alldata = [(s.exid, s.mid, s.id, s.name, s.padback[0][0],
                    s.padback[0][1],
                    s.padback[1][0], s.padback[1][1], s.padback[2][0],
                    s.padback[2][1], s.padback[3][0], s.padback[3][1],
                    s.padback[4][0], s.padback[4][1], s.padlay[0][0],
                    s.padlay[0][1], s.padlay[1][0], s.padlay[1][1],
                    s.padlay[2][0], s.padlay[2][1], s.padlay[3][0],
                    s.padlay[3][1], s.padlay[4][0], s.padlay[4][1],
                    s.src, s.wsn, tstamp)
                   for s in selections]

        # write to the current selections table; we have to do this
        # one entry at a time

        for d in alldata:
            try:
                self.cursor.execute(qins.format(schema.SELECTIONS), d)
            except sqlite3.IntegrityError:
                # already have (exchange_id, market_id, selection_id)
                # update prices
                self.cursor.execute(qupd, d[4:] + d[:3])

        # write to the historical prices table
        self.cursor.executemany(qins.format(schema.HISTPRICES), alldata)
            
        self.conn.commit()

    def WriteAccountBalance(self, exid, accinfo, tstamp):
        """Write account balance information to accountinfo table"""
        assert len(accinfo) == 4
        self.cursor.execute(('INSERT INTO {0} (exchange_id, available, '
                            'balance, credit, exposure, tstamp) values'
                            '(?, ?, ?, ?, ?, ?)'.format(schema.ACCOUNTINFO)),
                            (exid, accinfo[0], accinfo[1], accinfo[2],
                             accinfo[3], tstamp))
        self.conn.commit()

    def ReturnMarkets(self, sqlstr, sqlargs):
        """
        Execute query sqlquery, which should return a list of Markets.
        This convenience function will convert the database
        representation to a list of Market objects.
        """
        try:
            res = self.cursor.execute(sqlstr, sqlargs)
        except sqlite3.OperationalError:
            # query string was malformed somehow
            raise DBError, 'received malformed SQL statement'
        except ValueError:
            raise DBError, ('wrong parameters passed to SQL '
                                'statement')
        mdata = res.fetchall()
        # create Market objects from results of market data
        # pid and pname both None since we are not storing this info
        # in the database!
        # Note also we need to convert sqlite int into bool for
        # inrunning status of market.
        markets = [Market(m[2], m[1], None, bool(m[3]), None, m[0])
                   for m in mdata]
        
        return markets

    def ReturnOrders(self, sqlstr, sqlargs=None):
        """
        Execute query sqlquery, which should return a list of Orders.
        This convenience function will convert the database
        representation to a list of Order objects.
        """
        try:
            res = self.cursor.execute(sqlstr, sqlargs)
        except sqlite3.OperationalError:
            # query string was malformed somehow
            raise DBError, 'received malformed SQL statement'
        except ValueError:
            raise DBError, ('wrong parameters passed to SQL '
                                'statement')
        odata = res.fetchall()
        # create Order objects from results of market data
        # pid and pname both None since we are not storing this info
        # in the database!
        # Note also we need to convert sqlite int into bool for
        # inrunning status of market.
        orders = [Order(o[1], o[3], o[6], o[5], o[7], **{'oref': o[0],
                                                         'status': o[10],
                                                         'matchedstake': o[8],
                                                         'unmatchedstake': o[9],
                                                         'strategy': o[4],
                                                         'mid': o[2]})
                  for o in odata]
        
        return orders

    def ReturnSelections(self, sqlstr, sqlargs=None):
        """
        Execute query sqlquery, which should return a list of
        Selections.  This convenience function will convert the
        database representation to a list of Selection objects.
        """
        try:
            if sqlargs:
                res = self.cursor.execute(sqlstr, sqlargs)
            else:
                res = self.cursor.execute(sqlstr)
        except sqlite3.OperationalError:
            # query string was malformed somehow
            raise DBError, 'received malformed SQL statement'
        except ValueError:
            raise DBError, ('wrong parameters passed to SQL '
                                'statement')
        seldata = res.fetchall()
        # create Selection objects from results
        # we don't know a lot of info here since we are not storing
        # in the database:
        # mback
        # mlay
        # lastmatched
        # lastmatchedprice
        # lastmatchedamount
        selections = [Selection(s[3], s[2], s[1], None, None, None,
                                None, None,
                                # backprices and volumes
                                [y for y in util.pairwise(s[4:14])],
                                # layprices and volumes
                                [y for y in util.pairwise(s[14:24])],
                                s[24], # selection reset count
                                s[25], # withdrawal selection number
                                s[0])
                      for s in seldata]
        
        return selections

    def WriteMarkets(self, markets, tstamp):
        """Write to markets table"""

        # check  database is open
        if not self._isopen:
            self.open()
        
        data = [(m.exid, m.id, m.name, m.inrunning, tstamp)
                for m in markets]
        
        # if a row doesn't exist with this exchange id and market id
        # we insert it, otherwise we update (since inrunning could have
        # changed).  This is probably not the most efficient way of
        # accomplishing that.
        qins = ('INSERT INTO {0} (exchange_id, '
                'market_id, market_name, in_running,'
                'last_checked) values '
                '(?, ?, ?, ?, ?)'.format(schema.MARKETS))
        qupd = ('UPDATE {0} SET in_running=?,last_checked=? '
                'WHERE exchange_id=? and market_id=?'.\
                format(schema.MARKETS))
        
        for m in markets:
            try:
                self.cursor.execute(qins, (m.exid, m.id, m.name,
                                           m.inrunning, tstamp))
            except sqlite3.IntegrityError:
                # already have (exchange_id, market_id)
                # update inrunning status and timestamp
                self.cursor.execute(qupd, (m.inrunning, tstamp, m.exid,
                                           m.id))
        self.conn.commit()

    def WriteOrders(self, olist, tstamp):
        """Write to orders table"""

        # check  database is open
        if not self._isopen:
            self.open()

        # if a row doesn't exist with this order id we insert it,
        # otherwise we update.  This is probably not the most
        # efficient way of accomplishing that.
        qins = ('INSERT INTO {0} (order_id, '
                'exchange_id, market_id, selection_id,'
                'strategy, price, stake, polarity, matched,'
                'unmatched, status, tstamp) values '
                '(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)'.\
                format(schema.ORDERS))
        qupd = ('UPDATE {0} SET matched=?, unmatched=?, status=?,'
                'tstamp=? WHERE order_id=?').format(schema.ORDERS)
        
        for o in olist:
            # get default values for things not guaranteed to exist
            matched = getattr(o, 'matched', 0.0)
            unmatched = getattr(o, 'matched', o.stake)            
            status = getattr(o, 'status', order.UNMATCHED)
            strategy = getattr(o, 'strategy', None)

            try:
                self.cursor.execute(qins, (o.oref, o.exid, o.mid,
                                           o.sid, strategy, o.price,
                                           o.stake, o.polarity, matched,
                                           unmatched, status, tstamp))
            except sqlite3.IntegrityError:
                # already have order_id. Update matched amount,
                # unmatched amount, status and timestamp.
                self.cursor.execute(qupd, (matched, unmatched, status,
                                           tstamp, o.oref))
        self.conn.commit()
        
    def CreateTables(self):
        """Create all of the tables needed"""

        self.open()

        # exchanges table just stores number
        self.cursor.execute(schema.getschema(schema.EXCHANGES))
        exchanges = [(const.BDAQID, 'BetDAQ', 'www.betdaq.com'),
                     (const.BFID, 'BetFair', 'www.betfair.com')]
        self.conn.executemany('INSERT INTO {0} values (?, ?, ?)'.\
                              format(schema.EXCHANGES), exchanges)

        # matchingmarkets maps a market_id from one exchange to another
        self.cursor.execute(schema.getschema(schema.MATCHMARKS))

        # matchingselections maps a selection_id from one exchange to another
        # hopefully selections have unique numbers...
        self.cursor.execute(schema.getschema(schema.MATCHSELS))

        # the unique index ensures we don't have more than one row
        # with the same exchange_id and market_id
        self.cursor.execute('CREATE UNIQUE INDEX sindex ON {0}'
                            '(ex1_mid, ex1_sid)'.format(schema.MATCHSELS))

        # markets stores information about a market (but not selections)
        self.cursor.execute(schema.getschema(schema.MARKETS))

        # the unique index ensures we don't have more than one row
        # with the same exchange_id and market_id
        self.cursor.execute('CREATE UNIQUE INDEX mindex ON {0}'
                            '(exchange_id, market_id)'.format(schema.MARKETS))

        # selections stores market selections and their prices
        self.cursor.execute(schema.getschema(schema.SELECTIONS))

        # same unique index idea for selections table
        self.cursor.execute('CREATE UNIQUE INDEX pindex ON {0}'
                            '(exchange_id, market_id, selection_id)'\
                            .format(schema.SELECTIONS))

        # orders stores current orders, whether matched or not
        self.cursor.execute(schema.getschema(schema.ORDERS))

        # same unique index idea for orders table
        self.cursor.execute('CREATE UNIQUE INDEX oindex ON {0}'
                            '(exchange_id, order_id)'\
                            .format(schema.ORDERS))

        # matchorders stores pairs of orders
        self.cursor.execute(schema.getschema(schema.MATCHORDERS))

        # accountinfo stores balance, available funds etc
        self.cursor.execute(schema.getschema(schema.ACCOUNTINFO))

        # hist prices stores historical price information
        self.cursor.execute(schema.getschema(schema.HISTPRICES))

        self.conn.commit()
        return

    # TODO - Nothing below here is implemented yet.
    def check_ext(self):
        """External checks (makes API requests)"""
        return

    def check_match_tables(self):
        # check that the markets in MATCHMARKETS table are all
        # valid.  For markets that are not, we
        # i) delete the row from MATCHMARKETS table.
        # ii) delete any matching selection rows from MATCHSELS.
        return

    def cleanse(self):
        """Cleanse the database.
        WARNING: this deletes rows from various tables!"""

        # delete everything from tables:
        # MATCHMARKS
        # MATCHSELS
        # SELECTIONS

        for tname in [schema.MATCHMARKS, schema.MATCHSELS,
                      schema.SELECTIONS]:
            self.cursor.execute('DELETE FROM {0}'.format(tname))

        # delete all selections from SELECTIONS table (we only care
        # about the matching selections in MATCHSELS).
        self.cursor.execute('DELETE FROM {0}'.format(schema.SELECTIONS))
        
        self.conn.commit()
        return
