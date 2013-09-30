# getwinner.py
# James Mithen
# jamesmithen@gmail.com

"""Get winners of BDAQ horse racing markets by scraping BBC website"""

import urllib2
from HTMLParser import HTMLParser

class MyHTMLParser(HTMLParser):
    def __init__(self):

        HTMLParser.__init__(self)
        self.ncourses = 0
        # key to courses is the course name
        # value is a list [nraces, [[time, winner],...[time,winner]] ]
        self.courses = {}
        self.tnext = False
        self.wnext = False

    def return_winners(self, html):
        self.feed(html)
        return self.courses
        
    def handle_starttag(self, tag, attrs):
        if tag == 'h2':
            if attrs:
                if (attrs[0][0] == 'class'
                    and attrs[0][1] == 'table-header'):
                    # we found a new racecourse
                    self.ncourses += 1
        elif tag == 'td':
            if attrs:
                if (attrs[0][0] == 'class'
                    and attrs[0][1] == 'race-time'):
                    self.tnext = True
        elif tag == 'span':
            if attrs:
                if (attrs[0][0] == 'class'
                    and attrs[0][1] == 'horse pos1'):
                    self.wnext = True

    def handle_data(self, data):

        if self.ncourses:
            # add another course if we need to
            if self.ncourses > len(self.courses):
                self.courses[data] = {}
                self.curcourse = data

            # add another racing time if we need to
            if self.tnext:
                time = data.strip()
                self.tnext = False
                self.lasttime = time

            if self.wnext:
                self.courses[self.curcourse][self.lasttime] = data
                self.wnext = False

def getwinners(date, mnames):
    """
    mnames should be a list of market names like '20:30
    Kempton'. date should be e.g. 2013-09-25.
    """

    bbcurl = ('http://www.bbc.co.uk/sport/horse-racing/uk-ireland/'
              'results/{0}'.format(date.replace('-','')))
    data = urllib2.urlopen(bbcurl).read()
    
    # parse the html
    parser = MyHTMLParser()
    windict = parser.return_winners(data)

    winners = []
    for mname in mnames:
        time, course = mname.split()
        try:
            winners.append(windict[course][time])
        except KeyError:
            # winning time and course not successfully parsed from the
            # HTML.
            pass
    return winners
