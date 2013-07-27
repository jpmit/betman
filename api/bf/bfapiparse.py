# bfapiparse.py
# James Mithen
# jamesmithen@gmail.com
#
# functions for parsing the response that comes from the BF api

from betman import const, Market, Event

def ParseEvents(res):
    events = []
    for e in res.eventTypeItems.EventType:
        events.append(Event(e.name, e.id, 2))
    return events

def ParseMarkets(res):
    markets = []
    for mdata in res.marketData.split(':')[1:]:
        fields = mdata.split('~')
        # we will need to remove this erroneous Group D rubbish
        # at some point (!)        
        # fields are (in order, see also BF documentation):
        # [0] Market ID 
        # [1] Market name
        # [2] Market Type
        # [3] Market Status
        # [4] Event Date
        # [5] Menu Path
        # [6] Event Hierarchy (ids)
        # [7] Bet Delay
        # [8] Exchange Id (1 for UK/Worldwide, 2 for AUS)
        # [9] ISO3 Country code
        # [10] Last Refresh - time since cached data refreshed
        # [11] Number of Runners
        # [12] Number of Winners
        # [13] Total Amount Matched
        # [14] BSP Market
        # [15] Turning in Play

        # the full name of the market
        name = fields[5].replace('\\','|') + '|' + fields[1]
        myid = int(fields[0])
        # note parent id is the root one, we are skipping any
        # intermediate event ids
        pid = int(fields[6].split('/')[1])
        # are we inrunning?
        if fields[3] == 'ACTIVE':
            inrun = True
        else:
            inrun = False
        markets.append(Market(name, myid, pid, inrun, None, const.BFID))

    return markets
