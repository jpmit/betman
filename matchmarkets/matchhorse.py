# matchhorse.py
# James Mithen
# jamesmithen@gmail.com

import re
import time
import datetime
from betman.api.bf import bfapi
from betman import betlog

# conversion from BF course name to BDAQ course name.  BF course names
# on left, BDAQ course names on right.
COURSES = {'Ayr'   : 'Ayr',    
           'Bang'  : 'Bangor',
           'Bath'  : 'Bath',
           'Catt'  : 'Catterick',
           'Chelt' : 'Cheltenham',
           'Chest' : 'Chester',
           'Cork'  : 'Cork',
           'Curr'  : 'Curragh',
           # Deauville is a French course
           'Deau'  : 'Deauville',
           'Donc'  : 'Doncaster',
           'DownR' : 'Down Royal',
           'Kelso' : 'Kelso',           
           'Kemp'  : 'Kempton',
           # Kenilworth is in RSA
           'Kenil' : 'Kenilworth',
           'Ling'  : 'Lingfield',
           'List'  : 'Listowel',
           'Naas'  : 'Naas',
           'Newb'  : 'Newbury',
           'Newc'  : 'Newcastle',
           'Newm'  : 'Newmarket',           
           'Sand'  : 'Sandown',
           'Winc'  : 'Wincanton',
           'Wolv'  : 'Wolverhampton'}


def match_horse(bdaqmarkets, bfmarkets):
    """
    Return list of tuples (m1,m2) where m1 and m2 are the matching
    markets.
    """

    # we will only match 'win' markets, and not 'place markets'
    bdaqwinmarkets = [m for m in bdaqmarkets if
                      m.name.split('|')[-1] == 'Win Market']
    bdaqmarks = []
    for m in bdaqwinmarkets:
        names = m.name.split('|')
        stime = m.starttime
        course = names[-2][6:]
        m.course = course
        # add to list for comparison with BF
        bdaqmarks.append(m)

    # get dictionary of all the courses for BDAQ
    allcourses = {}
    for c in [m.course for m in bdaqmarks]:
        if c not in allcourses:
            allcourses[c] = None

    betlog.betlog.debug('Found BDAQ horse races for courses: {0}'\
                        .format(' '.join([c for c in allcourses])))

    # get all the BF races happening at one of these courses
    bfmarks = []
    for m in bfmarkets:
        names = m.name.split('|')
        # get course name
        cname = names[-2].split()[0]

        # try to map this to a bdaq course name
        try:
            bdaqcname = COURSES[cname]
        except KeyError:
            # don't have a matching bdaq course, so not interested in this
            # market
            continue
        else:
            m.course = bdaqcname

        if bdaqcname not in allcourses:
            # no BDAQ markets we would want to match with are happening on
            # this course
            continue
        
        # chop out any (AvB), (RFC), To Be Placed markets etc.
        if (('(AvB)' in names[-2]) or
            ('(RFC)' in names[-2]) or
            ('TBP' in names[-1]) or
            (names[-1] == 'To Be Placed') or
            (names[-1] == 'Without Fav(s)') or
            (names[-1] == 'Name The ISP Fav') or
            (names[2]  == 'ANTEPOST')):
            continue
        
        # we passed all the criteria: add to list of possible markets
        bfmarks.append(m)

    # go through each bdaq market in turn, try to find a matching bf
    # market.
    matchmarks = []
    for m1 in bdaqmarks:
        for m2 in bfmarks:
            # check races are happening on same course
            if m1.course == m2.course:
                # check start time of races are the same
                if m1.starttime == m2.starttime:
                    # same course and same start time, so same race
                    matchmarks.append((m1, m2))

    return matchmarks
