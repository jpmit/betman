# testorders.py
# an order dictionary that won't be matched

from betman import order, const

# six nations, england
o1 = order.Order(1, 17676144, 0.5, 100.0, 1, **{'mid': 3291920})
# six nations, wales
o2 = order.Order(1, 17676142, 0.5, 1.22, 2, **{'mid': 3291920})

#o2 = order.Order(2, 6550702, 2.0, 10.0, 1,
#                 **{'mid': 107586578, 'persistence': 'NONE'})
# red bull
#o3 = order.Order(1, 16375182, 0.5, 10.0, 1, **{'mid': 3046606})
#o4 = order.Order(2, 1002481, 2.0, 10.0, 1,
#                 **{'mid': 108021685, 'persistence': 'NONE'})

#od = {const.BDAQID: [o1], const.BFID: [o2]}
#od2 = {const.BDAQID: [o1, o3], const.BFID: [o2, o4]}
