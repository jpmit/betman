# main.py
# James Mithen
# jamesmithen@gmail.com
#
# get markets from BDAQ and BF

from betman.api.bf import bfapi
from betman.api.bdaq import bdaqapi

bfapi.Login()
bfevents = bfapi.GetActiveEvents()
bdaqevents = bdaqapi.GetTopLevelEvents()

# get markets for just a couple of event types
bfelist = ['Rugby Union', 'Motor Sport']
bdaqelist = ['Rugby Union']#, 'Formula 1']
bfmarkets = bfapi.GetUKMarkets([ev.id for ev in bfevents if ev.name in bfelist])
bdaqmarkets = bdaqapi.GetMarkets([ev.id for ev in bdaqevents if ev.name in bdaqelist])
