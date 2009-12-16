import logging
import os
import re
import urllib2
from BeautifulSoup import BeautifulSoup


from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext.webapp import template

class Address:
    def __init__(self):
        num = ''
        street = ''
        suffix = ''
        
    def __repr__(self):
        return self.num + ' ' + self.street + ' ' + self.suffix


class FetchHandler(webapp.RequestHandler):
    def get(self):
        self.response.headers['Content-Type'] = 'text/xml'
        addresses = self.request.get('addresses')
        addr = Address()
        addr.num = '14142'
        addr.street = 'Victory'
        addr.suffix = 'Bl'
        school = parseSchoolFinderResult(urllib2.urlopen(toURL(addr)))
        logging.info(school)
        if hasText(addresses):
            path = os.path.join(os.path.dirname(__file__), 'fetch.htm')
            self.response.out.write(template.render(path, {'addresses': addresses.split('|')}))
        else:
            path = os.path.join(os.path.dirname(__file__), 'fetch.htm')
            self.response.out.write(template.render(path, {}))

def parseSchool(school):
    try:
        return school('td')[1]('a')[0].string.replace('&nbsp;',' ')
    except:
        return 'invalid html format'

def parseSchoolFinderResult(page):
    soup = BeautifulSoup(''.join(page.readlines()))
    if re.search('NO MATCH WAS FOUND FOR ', str(soup)):
        return 'NO MATCH WAS FOUND'
    retval = ''
    for school in soup.findAll('table')[0]('tr'):
        if retval != '':
            retval = retval + '\n'
        retval = retval + parseSchool(school) 
    return retval

def toURL(address):
    return 'http://search.lausd.k12.ca.us/cgi-bin/fccgi.exe?Direction=(none)&w3exec=schfinder2&Submit=Submit&StreetName=%s&StreetNumber=%s&Suffix=%s' % ( address.street, address.num, address.suffix )

def hasText(str):
    """
    Returns True if the string argument is not empty.
    """
    return str != None and len(str.strip()) != 0

def main():
    urlmap = [
        # Maps /fetch.do -> FetchHandler
        ( '/fetch.do', FetchHandler ),
        # define additional mapping here
        ]
    application = webapp.WSGIApplication(urlmap, debug=True)
    run_wsgi_app(application)


if __name__ == '__main__':
    main()



# "C:\Program Files"\Google\google_appengine\dev_appserver.py
