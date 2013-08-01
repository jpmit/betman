# database.py
# James Mithen
# jamesmithen@gmail.com
#
# Interface for interacting with database

import os
import sqlite3
from betman import const, Market, Selection
from betman.all.betexception import DBException
import schemas

class DBMaster(object):
    """Simple interface to the main database"""
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

    def WriteSelectionMatches(self, selmatches):
        """Write to matchingselections table"""

        # check database is open
        if not self._isopen:
            self.open()

        # insertion stringo
        qins = ('INSERT INTO matchingselections (ex1_sid, ex1_name, ex2_sid'
                ', ex2_name) values (?,?,?,?)')

        for s1,s2 in selmatches:
            data = (s1.id, s1.name, s2.id, s2.name)
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
        # about SQL I shall come back to this.  Also, this is
        # vulnerable to SQL injection...

        # check database is open
        if not self._isopen:
            self.open()
        
        # first query matchingmarkets 
        qstr = 'SELECT * FROM matchingmarkets'
        qargs = ()
        if elist:
            # TODO: should check here that all the entries in elist
            # are valid BDAQ event names
            qargs = ['|'+elist[0]+'%']
            likestr = ' WHERE (ex1_name LIKE ?'
            # add
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
            ex1mark = self.ReturnMarkets('SELECT * FROM markets where '
                                         'exchange_id=? and market_id=?',
                                         (const.BDAQID, ex1mid))
            ex2mark = self.ReturnMarkets('SELECT * FROM markets where '
                                         'exchange_id=? and market_id=?',
                                         (const.BFID, ex2mid))
            matchmarkets.append((ex1mark[0], ex2mark[0]))
        return matchmarkets

    def WriteMarketMatches(self, matches):
        """Write to matchingmarkets table"""

        # check database is open
        if not self._isopen:
            self.open()

        # insertion string
        qins = ('INSERT INTO matchingmarkets (ex1_mid, ex1_name, ex2_mid'
                ', ex2_name) values (?,?,?,?)')

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
        qins = ('INSERT INTO selections (exchange_id, market_id, '
                'selection_id, name, b_1, bvol_1, b_2, bvol_2, b_3, '
                'bvol_3, b_4, bvol_4, b_5, bvol_5, lay_1, lvol_1, '
                'lay_2, lvol_2, lay_3, lvol_3, lay_4, lvol_4, '
                'lay_5, lvol_5, last_checked) values '
                '(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,'
                ' ?, ?, ?, ?, ?, ?, ?)')
        qupd = ('UPDATE selections SET b_1=?, bvol_1=?, b_2=?, bvol_2=?, '
                'b_3=?, bvol_3=?, b_4=?, bvol_4=?, b_5=?, bvol_5=?, '
                'lay_1=?, lvol_1=?, lay_2=?, lvol_2=?, lay_3=?, lvol_3=?, '
                'lay_4=?, lvol_4=?, lay_5=?, lvol_5=?, last_checked=? '
                'WHERE exchange_id=? and market_id=? and selection_id=?')
        
        for s in selections:
            data = (s.exid, s.mid, s.id, s.name, s.padback[0][0],
                    s.padback[0][1],
                    s.padback[1][0], s.padback[1][1], s.padback[2][0],
                    s.padback[2][1], s.padback[3][0], s.padback[3][1],
                    s.padback[4][0], s.padback[4][1], s.padlay[0][0],
                    s.padlay[0][1], s.padlay[1][0], s.padlay[1][1],
                    s.padlay[2][0], s.padlay[2][1], s.padlay[3][0],
                    s.padlay[3][1], s.padlay[4][0], s.padlay[4][1], tstamp)
            try:
                self.cursor.execute(qins, data)
            except sqlite3.IntegrityError:
                # already have (exchange_id, market_id, selection_id)
                # update prices
                self.cursor.execute(qupd, data[4:] + (s.exid, s.mid, s.id))
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
            raise DBException, 'received malformed SQL statement'
        except ValueError:
            raise DBException, ('wrong parameters passed to SQL '
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
            raise DBException, 'received malformed SQL statement'
        except ValueError:
            raise DBException, ('wrong parameters passed to SQL '
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
                                [y for y in util.pairwise(s[15:25])],
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
        qins = ('INSERT INTO markets (exchange_id, '
                'market_id, market_name, in_running,'
                'last_checked) values '
                '(?, ?, ?, ?, ?)')
        qupd = ('UPDATE markets SET in_running=?,last_checked=? '
                'WHERE exchange_id=? and market_id=?')
        
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

    def CreateTables(self):
        """Create all of the tables needed"""

        self.open()

        # exchanges table just stores number
        self.cursor.execute(schemas.getschema(schemas.EXCHANGES))
        exchanges = [(const.BDAQID, 'BetDAQ', 'www.betdaq.com'),
                     (const.BFID, 'BetFair', 'www.betfair.com')]
        self.conn.executemany('INSERT INTO {0} values (?, ?, ?)'.format(schemas.EXCHANGES),
                              exchanges)

        # matchingmarkets maps a market_id from one exchange to another
        self.cursor.execute(schemas.getschema(schema.MATCHMARKS)

        # matchingselections maps a selection_id from one exchange to another
        # hopefully selections have unique numbers...
        self.cursor.execute(schemas.getschema(schema.MATCHSELS))

        # markets stores information about a market (but not selections)
        self.cursor.execute(schemas.getschema(schema.MARKETS))

        # the unique index ensures we don't have more than one row
        # with the same exchange_id and market_id
        self.cursor.execute('CREATE UNIQUE INDEX mindex ON {0}'
                            '(exchange_id, market_id)'.format(schema.MARKETS))

        # selections stores market selections and their prices
        self.cursor.execute(schemas.getschema(schema.SELECTIONS))

        # same unique index idea for prices table
        self.cursor.execute('CREATE UNIQUE INDEX pindex ON {0}'
                            '(exchange_id, market_id, selection_id)'\
                            .format(schema.SELECTIONS))

        # orders stores current orders, whether matched or not
        self.cursor.execute(schemas.getshema(schema.ORDERS))

        self.conn.commit()
        return
