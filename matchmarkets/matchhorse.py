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
COURSES = {
           # Aqueduct is a US course
           'Aque'  : 'Aqueduct',
           'Aint'  : 'Aintree',
           'Ayr'   : 'Ayr',
           'Bang'  : 'Bangor',
           'Bath'  : 'Bath',
           'Catt'  : 'Catterick',
           # Charlestown is a US course
           'CharlT': 'Charles Town', 
           'Chelt' : 'Cheltenham',
           'Chest' : 'Chester',
           'Cork'  : 'Cork',
           'Curr'  : 'Curragh',
           # Deauville is a French course
           'Deau'  : 'Deauville',
           # Delta Downs is a US course
           'DeltaD': 'Delta Downs',
           'Donc'  : 'Doncaster',
           'DownR' : 'Down Royal',
           # Dundalk is in Ireland
           'Dund'  : 'Dundalk',
           # Greyville is in RSA
           'Grey'  : 'Greyville',
           # Gulf is a US course
           'Gulf'  : 'Gulfstream Park',
           'Kelso' : 'Kelso',           
           'Kemp'  : 'Kempton',
           # Kenilworth is in RSA
           'Kenil' : 'Kenilworth',
           # Leopardstown is in Ireland
           'Leop'  : 'Leopardstown',
           'Ling'  : 'Lingfield',
           'List'  : 'Listowel',
           'Ludl'  : 'Ludlow',
           'MrktR' : 'Market Rasen',
           'Naas'  : 'Naas',
           # Navan is in Ireland
           'Navan' : 'Navan',
           'Newb'  : 'Newbury',
           'Newc'  : 'Newcastle',
           'Newm'  : 'Newmarket',
           # Parx Racing is US
           'Parx'  : 'Parx Racing',
           # Pau is in France
           'Pau'   : 'Pau',
           # Punchestown is IRE
           'Punch' : 'Punchestown',
           'Plump' : 'Plumpton',
           # Sam Houston is US
           'SamH'  : 'Sam Houston',
           'Sand'  : 'Sandown',
           # Scottsville is RSA
           'Scots' : 'Scottsville',
           'Sthl'  : 'Southwell',
           # Sunland Park is US
           'SunP'  : 'Sunland Park',
           # Tampa Bay Downs is US
           'Tampa' : 'Tampa Bay Downs',
           # Toulouse is France
           'Toul' : 'Toulouse',
           # Turfway Park is US
           'Turf'  : 'Turfway Park',
           # Turffontein is RSA
           'Turf_R': 'Turffontein',
           # Turf Paradise is US
           'TPara' : 'Turf Paradise',
           'Winc'  : 'Wincanton',
           'Wolv'  : 'Wolverhampton'}

def match_horse(bdaqmarkets, bfmarkets):
    """
    Return list of tuples (m1,m2) where m1 and m2 are the matching
    markets.
    """

    # dicts with bdaq and bf courses as keys (values not needed)
    bf_courses = {i:None for i in COURSES.keys()}
    bdaq_courses = {i:None for i in COURSES.values()}

    # we will only match 'win' markets, and not 'place markets'
    bdaqwinmarkets = [m for m in bdaqmarkets if
                      m.name.split('|')[-1] == 'Win Market']
    bdaqmarks = []
    for m in bdaqwinmarkets:
        names = m.name.split('|')
        stime = m.starttime
        # extract course from BDAQ name

        # first, assume the race is named like so:
        # |Horse Racing|UK Racing|Wolverhampton (7th February 2014)|19:00 Wolverhampton|Win Market
        # getting the course is easy, we simply get all the text following the time.
        course = names[-2][6:]

        if course not in bdaq_courses:
            # ok, assume races names like so:
            # |Horse Racing|US Racing|Turfway Park (7th February 2014)|01:11 Turfway Park Race 5|Place Market
            # in which case we need to remove the 'Race 5' part
            mat = re.search('Race \d+', course)
            if mat:
                course = course[:mat.start() - 1]
            if course not in bdaq_courses:
                # finally, perhaps the race named like so:
                # |Horse Racing|Ante Post|Cheltenham (12th March 2014)|Neptune Novices Hurdle|Win Market
                # in which case we need to look at a level deeper
                # i.e. names[-3], and remove everything after the bracket (and the space before).
                course = names[-3]
                mat = re.search('\(', course)
                if mat:
                    course = course[:mat.start() - 1]

        # assign course to the market object
        m.course = course
        # add to list for comparison with BF
        bdaqmarks.append(m)

    # get dictionary of all the courses for BDAQ
    allcourses = {}
    for c in [m.course for m in bdaqmarks]:
        if c not in allcourses:
            allcourses[c] = None

    betlog.betlog.debug('Found BDAQ horse races for courses: {0}'\
                        .format('\n'.join([c for c in allcourses])))

    # get all the BF races happening at one of these courses
    bfmarks = []
    for m in bfmarkets:
        names = m.name.split('|')
        
        # get course name
        cname = names[-2].split()[0]

        # special cases 
        # we have a USA Turf and an RSA Turf, which are different
        # courses
        if (cname == 'Turf') and (names[-3] == 'RSA'):
            cname = 'Turf_R'

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
