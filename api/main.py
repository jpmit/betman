import apiclient
import apimethod

# create suds clients
# read-only
rcl = apiclient.APIClient('readonly')
scl = apiclient.APIClient('secure')

# get all the read only ones going like this
GetTopLevelEvents = apimethod.APIListTopLevelEvents(rcl).call
GetSubTree = apimethod.APIGetEventSubTreeNoSelections(rcl).call
# this one doesnt look very useful!
GetSubTreeSel = apimethod.APIGetEventSubTreeWithSelections(rcl).call
GetMarket = apimethod.APIGetMarketInformation(rcl).call
GetPrices = apimethod.APIGetPrices(rcl).call
GetSnum = apimethod.APIGetCurrentSelectionSequenceNumber(rcl).call
GetSelChangedSince = apimethod.APIListSelectionsChangedSince(rcl).call

# try some secure ones
GetBalance = apimethod.APIGetAccountBalances(scl).call
GetOrderDetails = apimethod.APIGetOrderDetails(scl).call
ListAccountPostings = apimethod.APIListAccountPostings(scl).call
ListBoot = apimethod.APIListBootstrapOrders(scl).call

# note there is an event classified id and a market id
events = GetTopLevelEvents()
# rugby union
#stree = GetSubTreeSel([events[7].id])
# lions series winner
#mark = GetMarket([3201204])
#price = GetPrices([3201204])
