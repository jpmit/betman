"""Command line controller for betting app.

This will load an automation and run using the engine until finished.

"""

import const
from betman.core import engine, config
from betman.core.automation import hautomation
import models
from betman import clock

# configure engine and clock
conf = config.GlobalConfig(const.CFGFILE)
eng = engine.Engine(conf)
clk = clock.Clock(const.TICK_LENGTH_MS / 1000.0)
# first tick initialises clock
clk.tick()

# make sure we have up to date matching markets (slightly hackish
# since the model is really designed for the GUI)
mmod = models.MatchMarketsModel.Instance()
mmod.Update('Horse Racing', True)

# get automation to the engine
eng.add_automation(hautomation.MyAutomation())

# main loop
while 1:
    # do everything
    eng.tick()

    # delay for the correct time
    clk.tick()
