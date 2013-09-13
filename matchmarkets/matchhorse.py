# matchhorse.py
# James Mithen
# jamesmithen@gmail.com

# Try to match markets for horse racing. Note: This calls some BF API
# functions.

import re
import time
import datetime
from betman.api.bf import bfapi
from betman import betlog

# conversion from BF course name to BDAQ course name
COURSES = {'Donc'  : 'Doncaster',
           'Bang'  : 'Bangor',
           'Sand'  : 'Sandown',
           'Wolv'  : 'Wolverhampton',
           'DownR' : 'Down Royal',
           'Bath'  : 'Bath',
           'Chest' : 'Chester',
           'Kemp'  : 'Kempton',
           'Curr'  : 'Curragh'}

def MatchHorse(bdaqmarkets, bfmarkets):
    """Return list of tuples (m1,m2) where m1 and m2 are the matching
    markets"""

    # we will only match 'win' markets, and not 'place markets'
    bdaqwinmarkets = [m for m in bdaqmarkets if
                      m.name.split('|')[-1] == 'Win Market']
    bdaqmarks = []
    for m in bdaqwinmarkets:
        names = m.name.split('|')
        stime = names[-2][:5]
        course = names[-2][6:]
        date = re.findall('\(.+\)', names[-3])[0][1:-1]
        # replace th and st in e.g. 13th September
        date = date.replace('th','')

        try:
            # convert date into datetime object
            dt = datetime.datetime.strptime(stime + ' ' + date,
                                            '%H:%M %d %B %Y')
        except:
            # there must not have been any time given
            pass
        else:
            m.course = course
            m.starttime = dt
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
            (names[-1] == 'To Be Placed') or
            (names[-1] == 'Without Fav(s)') or
            (names[-1] == 'Name The ISP Fav')):
            continue
        bfmarks.append(m)

    # for each of these bf markets, get the starttime from
    # resp.Market.marketDisplayTime, and the number of winners from
    # resp.Market.numberofWinners
    bfapi.Login()

    betlog.betlog.debug(('Checking market info for {0} BF markets '
                         'to match horse racing markets'.format(len(bfmarks))))
    for m in bfmarks:
        resp = bfapi.GetMarket(m.id)

        # we may want to use marketDisplayTime here instead
        m.starttime = resp.market.marketTime
        # numwinnders should be 1 for all markets
        m.numwinners = resp.market.numberOfWinners

        # can only call this 5 times per minute so wait 13 secs here to be
        # safe!
        time.sleep(13)

    # if we are in BST (British Summer Time), then convert time to BST
    # (local) time from GMT.
    for m in bfmarks:
        m.starttime = m.starttime + datetime.timedelta(hours=1)

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
