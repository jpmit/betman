# clock.py
# James Mithen
# jamesmithen@gmail.com

"""Simple Clock class for controlling how often we pass through a
 loop.  Similar idea to pygame.clock!
"""

import time

class Clock(object):
    def __init__(self, deltat):

        """Create new clock object with interval deltat.

        Note this is not intended for precision use.  deltat should be
        given in seconds.

        """

        self.deltat = deltat
        # only start the timing after first call to self.tick()
        self.running = False

    def tick(self):
        if not self.running:
            self.lasttime = time.time()
            self.running = True
            return
        # get the current time
        curtime = time.time()
        # if the current time is
        if curtime > self.lasttime + self.deltat:
            self.lasttime = curtime
            return
        # otherwise sleep for the correct number of seconds
        else:
            sleeptime = self.deltat - (curtime - self.lasttime)
            time.sleep(sleeptime)
            self.lasttime = curtime + sleeptime
            return

    def stop(self):
        self.running = False
