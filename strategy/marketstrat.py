# marketstrat.py
# 24th June 2013
# the basic market making strategy

import numpy as np
import pylab as P

s_L = 1.00
c_L = 0.05
c_B = 0.05
o_L = 4.8
o_B = 5.7

# check if there is an 'arbitrage' (market making) opportunity

if (o_B <= o_L/((1 - c_L)*(1 - c_B))):
    print "no arbitrage opportunity"

# compute upper limit and lower limit backing stakes
s_B_min = s_L * o_L / (o_B * (1 - c_B))
s_B_max = s_L * (1 - c_L)

# compute profit if selection wins, and profit if selection loses as a
# function of s_B between the two limits.

s_Bvals = np.linspace(s_B_min, s_B_max, 100, endpoint=True)
P_win = s_Bvals*o_B*(1 - c_B) - s_L*o_L
P_loss = s_L*(1 - c_L) - s_Bvals

# plot the results
P.plot(s_Bvals, P_win, label='win')
P.plot(s_Bvals, P_loss, label='loss')
P.legend()

