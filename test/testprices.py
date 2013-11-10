# testprices.py
# James Mithen
# jamesmithen@gmail.com

"""
Check that the prices from the APIs match the prices obtained by
screen scraping.
"""

from betman.api.bf import bfapi
from betman.api.bdaq import bdaqapi

# we will need to replace the mids with in running (Horse Racing)
# markets to really test the difference betwen 'screen scraping' and
# using the API prices.

# these mids are for premier league winner 2014!
bdaq_mid = 3213933
bf_mid = 109165222

# need to call these functions at the same time
