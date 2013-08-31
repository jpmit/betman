# exchangedata.py
# James Mithen
# jamesmithen@gmail.com
#
# Some information for the exchanges

# same for both BDAQ and BF
MINODDS = 1.0
MAXODDS = 1000.0

# consecutive odds for min odds (again same for both exchanges).  This
# is useful for knowing when the order book is empty.
MINODDSPLUS1 = 1.01

# Allowed odds for BDAQ data
# --------------------------
# Increments below obtained by testing betdaq.com on 4th August
# 1 	   3 	   0.01
# 3.05 	4 	   0.05
# 4.1 	6 	   0.1
# 6.2 	10 	0.2
# 10.5 	20 	0.5
# 21 	   50 	1
# 52     200   2
# 200    1000  5

# Allowed odds for BF data
# ------------------------
# Table below taken from
# http://help.betfair.info/contents/itemId/i65767327/index.en.html on
# 4th August 2013 : 
# From 	To 	Increment
# 1 	   2 	   0.01
# 2.02 	3 	   0.02
# 3.05 	4 	   0.05
# 4.1 	6 	   0.1
# 6.2 	10 	0.2
# 10.5 	20 	0.5
# 21 	   30 	1
# 32 	   50 	2
# 55 	   100 	5
# 110 	1000 	10
# 1000+ 	   Not Allowed
# The odds increment on Asian Handicap markets is 0.01 for all odds
# ranges.
