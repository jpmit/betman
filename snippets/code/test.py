# test.py

import apiclient
import apimethod
import datetime

# create suds clients
# read-only
rcl = apiclient.APIClient('readonly')
# secure
scl = apiclient.APIClient('secure')

# try backing Australia to win series at 6.0 for 50p !!!
from testorder import order

PlaceOrder = apimethod.APIPlaceOrdersWithReceipt(scl).call
res = PlaceOrder(order)

#GetBalance = apimethod.APIGetAccountBalances(scl).call
#res = GetBalance()

# order handle 1845831562
#GetOrder = apimethod.APIGetOrderDetails(scl).call
#res = GetOrder(1845831562)
