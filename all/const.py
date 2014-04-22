# const.py
# James Mithen
# jamesmithen@gmail.com

"""Some constants that are useful globally."""

import suds
import sys
import os

# version number for this software
VERSION='0.1'

# print debugging information to stdout while running code?
DEBUG = True

# send as 'user-agent' header for all SOAP requests
USERAGENT = 'pybetman/%s Python/%s Suds/%s' %(VERSION,
                                              sys.version.split()[0],
                                              suds.__version__)

# for relative links to files below
_RPATH=os.path.normpath(os.path.join(os.path.dirname(__file__), '..'))

# path to local copy of WSDL files
WSDLLOCAL = {'BDAQ'    : 'file:///{0}/api/bdaq/API.wsdl'.format(_RPATH),
             'BFglobal': 'file:///{0}/api/bf/BFGlobalService.wsdl'.format(_RPATH),
             'BFuk'    : 'file:///{0}/api/bf/BFExchangeServiceUK.wsdl'.format(_RPATH),
             'BFaus'   : 'file:///{0}/api/bf/BFExchangeServiceAUS.wsdl'.format(_RPATH)}

# BDAQ API version sent in SOAP headers
BDAQAPIVERSION = '2'

# BDAQ username and password
BDAQUSER = 'jimmybob'
BDAQPASS = 'Alm0stTheEnd0fTheW0rld'

# BF username and password
BFUSER = 'mithen'
BFPASS = 'Bamb0[]zle'

# path to database
MASTERDB = '{0}/database/masterdb.db'.format(_RPATH)

# path to log files
LOGDIR = '{0}/logs/'.format(_RPATH)

# write to database after results of every API call?
WRITEDB = False

# exchange ids of BDAQ and BF
BDAQID = 1
BFID = 2

# number of back and lay prices to ask for and store
# note this is hard-coded into the database schema so
# don't change this number.
NUMPRICES = 5
