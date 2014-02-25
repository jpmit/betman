from itertools import izip
import const

def chunks(li, n):
    """Yield successive n-sized chunks from li."""
    for i in xrange(0, len(li), n):
        yield li[i:i+n]

def pairwise(iterable):
    """s -> (s0,s1), (s2,s3), (s4, s5), ..."""
    a = iter(iterable)
    return izip(a, a)

def unique(seq):
   """Return sequence with duplicates removed (order preserving)"""
   seen = {}
   result = []
   for item in seq:
       if item in seen:
           continue
       seen[item] = 1
       result.append(item)
   return result

# this is for adding two dictionaries with exids as keys and lists as values
cdict = lambda d1, d2: {const.BDAQID: d1.get(const.BDAQID, []) + d2.get(const.BDAQID, []), 
                          const.BFID: d1.get(const.BFID, []) + d2.get(const.BFID, [])}

# flatten a dictionary with exids as keys and orefs as values into a
# single flat list.  Useful e.g. for order dict {const.BDAQID:
# {oref11: o11, oref12: o12}, const.BFID: {oref21: o21, oref22: o22},
# in this case the result will be a single list [o11, o12, o21, o22]
flattendict = lambda d: [i for sl in [o.values() for o in d.values()] for i in sl]
