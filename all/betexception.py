# betexception.py
# James Mithen
# jamesmithen@gmail.com

"""
Exception classes for the entire code.  These are empty at the moment
so are purely here for the descriptive names only.
"""

# base class for everything
class BetmanError(Exception): pass

class DbError(BetmanError): pass

class DbCorruptError(DbError) : pass

class DataError(BetmanError): pass

class ApiError(BetmanError): pass

# for errors when trying to match selections and markets
class MatchError(BetmanError): pass

