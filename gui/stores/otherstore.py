"""All other stores except for OrderStore and Pricing Store.

At present we have a MarketStore, which stores details of the markets
for both BDAQ and BF (including mapping between mids), and a
SelectionStore, which does the same for selections.  The
SelectionStore also stores the display order of the selections.

"""

@Singleton
class MarketStore(object):
    pass


@Singleton
class SelectionStore(object):
    pass

