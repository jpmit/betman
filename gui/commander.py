"""Command line controller for betting app.

This will load an automation and run using the engine until finished.

"""

import const
from betman.core import engine, config
from betman.core.automation import hautomation
from betman.core.stores import updaters
from betman import clock

# configure engine and clock
conf = config.GlobalConfig(const.CFGFILE)
eng = engine.Engine(conf)
clk = clock.Clock(const.TICK_LENGTH_MS / 1000.0)
# first tick initialises clock
clk.tick()

# update matching markets for horse racing
mupd = updaters.MarketUpdater.Instance()
mupd.update_market_information('Horse Racing')

# get automation to the engine
eng.add_automation(hautomation.MyAutomation())

# main loop
while 1:
    # do everything
    eng.tick()

    # delay for the correct time
    clk.tick()
