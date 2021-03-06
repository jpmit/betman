# schemas.py
# James Mithen
# jamesmithen@gmail.com

"""
Schemas for SQL tables. These are stored here for easy access in case
of future modification.
"""

from betman.all.betexception import DbError

# table names
EXCHANGES = 'exchanges'
MATCHMARKS = 'matchmarkets'
MATCHSELS = 'matchselections'
MARKETS = 'markets'
SELECTIONS = 'selections'
ORDERS = 'orders'
MATCHORDERS = 'matchorders'
ACCOUNTINFO = 'accountinfo'
HISTSELECTIONS = 'histselections'
HISTORDERS = 'historders'

# keys are table name, value is schema
_SQLSCHEMA = {EXCHANGES:  ('(id   integer primary key,'
                           ' name text NOT NULL,'
                           ' url  text NOT NULL)'),
              MATCHMARKS: ('(ex1_mid  long primary key,'
                           ' ex1_name text NOT NULL,'
                           ' ex2_mid  long NOT NULL,'
                           ' ex2_name text NOT NULL)'),
              MATCHSELS:  ('(ex1_mid  long NOT NULL,'
                           ' ex1_sid  long NOT NULL,'
                           ' ex1_name text NOT NULL,'
                           ' ex2_mid  long NOT NULL,'
                           ' ex2_sid  long NOT NULL,'
                           ' ex2_name text NOT NULL)'),
              MARKETS:    ('(exchange_id   int       NOT NULL,'
                           ' market_id     long      NOT NULL,'
                           ' market_name   text      NOT NULL,'
                           # total matched is allowed to be null since
                           # the BDAQ API doesn't return this.
                           ' total_matched real,'
                           ' in_running    bool      NOT NULL,'
                           ' start_time    timestamp NOT NULL,'
                           ' last_checked  timestamp NOT NULL)'),
              # might only actually want more like 3 back and lay
              # prices later on.
              SELECTIONS: ('(exchange_id  int  NOT NULL,'
                           ' market_id    long NOT NULL,'
                           ' selection_id long NOT NULL,'
                           ' name         text NOT NULL,'
                           ' b_1          real,'
                           ' bvol_1       real,'
                           ' b_2          real,'
                           ' bvol_2       real,'
                           ' b_3          real,'
                           ' bvol_3       real,'
                           ' b_4          real,'
                           ' bvol_4       real,'
                           ' b_5          real,'
                           ' bvol_5       real,'
                           ' lay_1        real,'
                           ' lvol_1       real,'
                           ' lay_2        real,'
                           ' lvol_2       real,'
                           ' lay_3        real,'
                           ' lvol_3       real,'
                           ' lay_4        real,'
                           ' lvol_4       real,'
                           ' lay_5        real,'
                           ' lvol_5       real,'
                           # selection reset count (needed for placing
                           # bet on BDAQ, NULL for BF)
                           ' src          int,'
                           # withdrawal selection number (needed for
                           # placing bet on BDAQ, NULL for BF)
                           ' wsn          int,'
                           # display order of selections (from BDAQ
                           # API). note this is not returned by
                           # GetPrices, but by GetMarketInformation,
                           # so it is likely to be set by updating a
                           # currently existing selection.
                           ' dorder       int,'
                           ' tstamp       timestamp)'),
              # strategy is the strategy type
              # polarity can be either 1 (back) or 2 (lay)
              # matched is the amount (up to stake) that has been matched
              # order status can be:
              # 1 - INPLAY
              # 2 - WAITING
              # 3 - MATCHED
              # 4 - CANCELLED
              ORDERS:     ('(order_id     int  primary key, '
                           ' exchange_id  int  NOT NULL,'
                           ' market_id    long,         '
                           ' selection_id long NOT NULL,'
                           ' strategy     int,'
                           ' price        real NOT NULL,'
                           ' stake        real NOT NULL,'
                           ' polarity     int  NOT NULL,'
                           ' matched      real NOT NULL,'
                           ' unmatched    real NOT NULL,'
                           ' status       int  NOT NULL,'
                           ' tplaced      timestamp NOT NULL,'
                           ' tstamp       timestamp NOT NULL)'),
              MATCHORDERS: ('(order1_id   int  primary key, '
                            ' order2_id   int  NOT NULL, '
                            ' tplaced     text NOT NULL)'),
              ACCOUNTINFO: ('(exchange_id int  NOT NULL, '
                            ' available   real NOT NULL,'
                            ' balance     real NOT NULL,'
                            ' credit      real NOT NULL,'
                            ' exposure    real NOT NULL,'
                            ' tstamp      timestamp NOT NULL)'),
              # HISTSELECTIONS has the same schema as SELECTIONS
              HISTSELECTIONS: \
                           ('(exchange_id  int  NOT NULL,'
                            ' market_id    long NOT NULL,'
                            ' selection_id long NOT NULL,'
                            ' name         text NOT NULL,'
                            ' b_1          real,'
                            ' bvol_1       real,'
                            ' b_2          real,'
                            ' bvol_2       real,'
                            ' b_3          real,'
                            ' bvol_3       real,'
                            ' b_4          real,'
                            ' bvol_4       real,'
                            ' b_5          real,'
                            ' bvol_5       real,'
                            ' lay_1        real,'
                            ' lvol_1       real,'
                            ' lay_2        real,'
                            ' lvol_2       real,'
                            ' lay_3        real,'
                            ' lvol_3       real,'
                            ' lay_4        real,'
                            ' lvol_4       real,'
                            ' lay_5        real,'
                            ' lvol_5       real,'
                            ' src          int,'
                            ' wsn          int,'
                            ' dorder       int,'
                            ' tstamp       timestamp)'),
              # HISTORDERS has the same schema as ORDERS
              HISTORDERS:     ('(order_id     int  NOT NULL, '
                               ' exchange_id  int  NOT NULL,'
                               ' market_id    long,         '
                               ' selection_id long NOT NULL,'
                               ' strategy     int,'
                               ' price        real NOT NULL,'
                               ' stake        real NOT NULL,'
                               ' polarity     int  NOT NULL,'
                               ' matched      real NOT NULL,'
                               ' unmatched    real NOT NULL,'
                               ' status       int  NOT NULL,'
                               # note tplaced can be null in this
                               # table, though it can't be null in
                               # ORDERS table.
                               ' tplaced      timestamp,'
                               ' tstamp       timestamp NOT NULL)')              
              }

def getschema(tname):
    """Get string for creating table for particular table name."""

    if tname not in _SQLSCHEMA:
        raise DbException, 'table name {0} has no schema'\
              .format(tname)
    return '{0} {1} {2}'.format('CREATE TABLE', tname, _SQLSCHEMA[tname])
