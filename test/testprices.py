# testprices.py
# James Mithen
# jamesmithen@gmail.com

"""
Check that the prices from the APIs match the prices obtained by
screen scraping.  And test multithreading/mulitprocessing!
"""

from betman import const
from betman.api.bf import bfapi
from betman.api.bdaq import bdaqapi
from threading import Thread
from Queue import Queue

# we will need to replace the mids with in running (Horse Racing)
# markets to really test the difference betwen 'screen scraping' and
# using the API prices.

# these mids are for premier league winner 2014!
bdaq_mid = 3213933
bf_mid = 109165222


q = Queue()
results = {}
emids = {}

def worker():
    while True:
        func, mids, myid = q.get()
        results[myid], emids[myid] = func(mids)
        q.task_done()

for i in range(2):
    t = Thread(target = worker)
    t.setDaemon(True)
    t.start()

q.put((bdaqapi.GetPrices_nApi, [bdaq_mid], const.BDAQID))
q.put((bfapi.GetPrices_nApi, [bf_mid], const.BFID))
q.join()
# need to call these functions at the same time
#bdprices = bdaqapi.GetPrices_nApi([bdaq_mid])
#bfprices = bfapi.GetPrices_nApi([bf_mid])
