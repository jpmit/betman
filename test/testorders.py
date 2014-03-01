# testorders.py
# an order dictionary that won't be matched

from betman import order, const

# BDAQ
# six nations, england
o1 = order.Order(1, 17676144, 0.5, 100.0, 1, **{'mid': 3291920})
# six nations, wales
o2 = order.Order(1, 17676142, 0.5, 1.22, 2, **{'mid': 3291920})

# BF
# six nations, england
o3 = order.Order(1, 15593, 2.0, 10.0, 1, **{'mid': 109590806, 
                                            'persistence': 'NONE'})
# six nations, wales
o4 = order.Order(2, 14118, 2.05, 10.0, 1, **{'mid': 109590806, 
                                            'persistence': 'NONE'})
d = {1: [], 2: []}

