# schemas.py
# James Mithen
# jamesmithen@gmail.com
#
# Schemas for SQL tables. These are stored here for easy access in
# case of future modification.

from betman.all.betexception import DBError

# table names
EXCHANGES = 'exchanges'
MATCHMARKS = 'matchmarkets'
MATCHSELS = 'matchselections'
MARKETS = 'markets'
SELECTIONS = 'selections'
ORDERS = 'orders'
MATCHORDERS = 'matchorders'

# keys are table name, value is schema
_SQLSCHEMA = {EXCHANGES:  ('(id integer primary key, name text, url '
                            'text)'),
              MATCHMARKS: ('(ex1_mid long primary key, '
                           'ex1_name text, ex2_mid long, '
                           'ex2_name text)'),
              MATCHSELS:  ('(ex1_mid long NOT NULL, ex1_sid long NOT NULL, ex1_name text,'
                           ' ex2_mid long NOT NULL, ex2_sid long NOT NULL, ex2_name text)'),
              MARKETS:    ('(exchange_id int NOT NULL, market_id long '
                           'NOT NULL, market_name text, in_running bool, '
                           'last_checked text)'),
              # might only actually want more like 3 back and lay
              # prices later on.
              SELECTIONS: ('(exchange_id int, market_id long,'
                           'selection_id long, name text, '
                           'b_1 real, bvol_1 real,'
                           'b_2 real, bvol_2 real, b_3 real,'
                           'bvol_3 real, b_4 real, bvol_4 real,'
                           'b_5 real, bvol_5 real, lay_1 real,'
                           'lvol_1 real, lay_2 real, lvol_2 real,'
                           'lay_3 real, lvol_3 real, lay_4 real,'
                           'lvol_4 real, lay_5 real, lvol_5 real,'
                           'last_checked text)'),
              # strategy is the strategy type
              # polarity can be either 1 (back) or 2 (lay)
              # matched is the amount (up to stake) that has been matched
              # order status can be:
              # 1 - INPLAY
              # 2 - WAITING
              # 3 - MATCHED
              # 4 - CANCELLED
              ORDERS:     ('(exchange_id int NOT NULL, '
                           'market_id long NOT NULL,'
                           'selection_id long NOT NULL, strategy int,'
                           'price real NOT NULL, stake real NOT NULL,'
                           'polarity int NOT NULL,matched real, '
                           'status int NOT NULL)'),
              MATCHORDERS: ('(order1_id int NOT NULL primary key, '
                            'order2_id int NOT NULL)')
              }

def getschema(tname):
    """Get string for creating table for particular table name"""
    if tname not in _SQLSCHEMA:
        raise DBException, 'table name {0} has no schema'\
              .format(tname)
    return '{0} {1} {2}'.format('CREATE TABLE', tname,
                                _SQLSCHEMA[tname])
