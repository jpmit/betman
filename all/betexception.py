# betexception.py
# James Mithen
# jamesmithen@gmail.com
#
# Exception classes for the entire code

class DBError(Exception): pass

class DBCorruptError(DBError) : pass
