# order.py
# James Mithen
# jamesmithen@gmail.com

# Order objects for exchange

class Order(object):
    """Returned after an order is placed"""
    def __init__(self, exid, sid, stake, price, polarity, orderref):
        self.exid = exid
        self.sid = sid
        self.stake = stake
        self.price = price
        self.polarity = polarity # 1 for back, 2 for lay
        self.oref = orderref

class PlaceOrder(object):
    """PlaceOrder holds info necessary to place an order"""
    def __init__(self, exid, sid, stake, price, polarity):
        self.exid = exid
        self.sid = sid
        self.stake = stake
        self.price = price
        self.polarity = polarity # 1 for back, 2 for lay
