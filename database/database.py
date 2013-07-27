import os
import sqlite3
from betman import const, Market, Selection

class DBException(Exception): pass

class DBMaster(object):
    """Simple interface to the main database"""
    def __init__(self, create=False):
        self.open()
        self.CreateIfNotExist()

    def CreateIfNotExist(self):
        """Create the database if it doesn't already exist"""
        if not os.path.exists(const.MASTERDB):
            self.CreateTables()

    def open(self):
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

        # exchanges table just stores number
        self.cursor.execute(('CREATE TABLE exchanges '
                             '(id integer primary key, name text, url '
                             'text)'))
        exchanges = [(const.BDAQID, 'BetDAQ', 'www.betdaq.com'),
                     (const.BFID, 'BetFair', 'www.betfair.com')]
        self.conn.executemany('INSERT INTO exchanges values (?, ?, ?)',
                              exchanges)

        # matchingmarkets maps a market_id from one exchange to another
        self.cursor.execute(('CREATE TABLE matchingmarkets '
                             '(ex1_mid long primary key, ex1_name text,'
                             'ex2_mid long, ex2_name text)'))

        # matchingselections maps a selection_id from one exchange to another
        # hopefully selections have unique numbers...
        self.cursor.execute(('CREATE TABLE matchingselections '
                             '(ex1_sid long primary key, ex1_name text,'
                             'ex2_sid long NOT NULL, ex2_name text)'))

        # markets stores information about a market (but not selections)
        self.cursor.execute(('CREATE TABLE markets '
                             '(exchange_id int NOT NULL, '
                             'market_id long NOT NULL,'
                             'market_name text, '
                             'in_running bool, '
                             'last_checked text)'))

        # the unique index ensures we don't have more than one row
        # with the same exchange_id and market_id
        self.cursor.execute('CREATE UNIQUE INDEX mindex ON markets'
                            '(exchange_id, market_id)')

        # selections stores market selections and their prices
        self.cursor.execute(('CREATE TABLE selections '
                             '(exchange_id int, market_id long,'
                             'selection_id long, name text, '
                             'b_1 real, bvol_1 real,'
                             'b_2 real, bvol_2 real, b_3 real,'
                             'bvol_3 real, b_4 real, bvol_4 real,'
                             'b_5 real, bvol_5 real, lay_1 real,'
                             'lvol_1 real, lay_2 real, lvol_2 real,'
                             'lay_3 real, lvol_3 real, lay_4 real,'
                             'lvol_4 real, lay_5 real, lvol_5 real,'
                             'last_checked text)'))

        # same unique index idea for prices table
        self.cursor.execute('CREATE UNIQUE INDEX pindex ON selections'
                            '(exchange_id, market_id, selection_id)')

        # orders stores current orders, whether matched or not
        self.cursor.execute(('CREATE TABLE orders '
                             '(exchange_id int, market_id long,'
                             'selection_id long, strategy int,'
                             'price real, stake real, polarity int,'
                             'matched real)'))

        self.conn.commit()
        return

def StorePrice(mid, timestamp, prices):
    conn = sqlite3.connect('prices.db')
    c = conn.cursor()
    c.execute('INSERT INTO prices VALUES (?,?,?)',
              (mid, timestamp, str(prices)))
    conn.commit()
    return

def RetreiveAllPrices():
    conn = sqlite3.connect('prices.db')
    c = conn.cursor()
    c.execute('SELECT * FROM prices')
    conn.commit()
    return c.fetchall()
