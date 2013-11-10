# const.py
# James Mithen
# jamesmithen@gmail.com

"""Some constants that are useful globally."""

import suds
import sys

# version number for this software
VERSION='0.1'

# print debugging information to stdout while running code?
DEBUG = True

# send as 'user-agent' header for all SOAP requests
USERAGENT = 'pybetman/%s Python/%s Suds/%s' %(VERSION,
                                              sys.version.split()[0],
                                              suds.__version__)

# path to local copy of WSDL files
WSDLLOCAL = {'BDAQ'    : ('file:///home/jm0037/python/bdaq/code'
                          '/betman/api/bdaq/API.wsdl'),
             'BFglobal': ('file:///home/jm0037/python/bdaq/code'
                          '/betman/api/bf/BFGlobalService.wsdl'),
             'BFuk'    : ('file:///home/jm0037/python/bdaq/code/'
                          'betman/api/bf/BFExchangeServiceUK.wsdl'),
             'BFaus'   : ('file:///home/jm0037/python/bdaq/code/'
                          'betman/api/bf/BFExchangeServiceAUS.wsdl')}

# BDAQ API version sent in SOAP headers
BDAQAPIVERSION = '2'

# BDAQ username and password
BDAQUSER = 'jimmybob'
BDAQPASS = 'Alm0stTheEnd0fTheW0rld'

# BF username and password
BFUSER = 'mithen'
BFPASS = 'Bamb0[]zle'

# path to database
MASTERDB = '/home/jm0037/python/bdaq/code/betman/database/masterdb.db'

# path to log files
LOGDIR = '/home/jm0037/python/bdaq/code/betman/logs/'

# write to database after results of every API call?
WRITEDB = True

# exchange ids of BDAQ and BF
BDAQID = 1
BFID = 2

# number of back and lay prices to ask for and store
# note this is hard-coded into the database schema so
# don't change this number.
NUMPRICES = 5
