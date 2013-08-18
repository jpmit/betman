# betmain.py
# James Mithen
# jamesmithen@gmail.com
#
# Main betting script.  Here we assume we have the matching markets
# and the matching selections already in the database, we just need to
# poll the prices regularly and check for any opportunities etc.

from betman import database

# get the matching selections
msels = dbman.ReturnSelectionMatches()
