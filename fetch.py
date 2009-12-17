import logging
import os
import re
import urllib2
from BeautifulSoup import BeautifulSoup


from google.appengine.ext import db
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext.webapp import template


SUFFIX_MAP = [
    [['blvd','bl','boulevard'],'Bl'],
    [['terrace','te','boulevard'],'Te'],
    [['street','st'],'St'],
    [['avenue','ave','av'],'Av'],
    [['drive','dr'],'Dr'],
    [['place','pl'],'Pl'],
    [['plaza','pz'],'Pz'],
    [['road','rd'],'Rd'],
    [['lane','ln'],'Ln'],
    [['way','wy'],'Wy']
]
def map_suffix(suffix):
    suffix = suffix.lower()
    for elem in SUFFIX_MAP:
        if suffix in elem[0]:
            return elem[1]
    return suffix

class Address():
    def __init__(self):
        self.num = None
        self.street = None
        self.suffix = None
        self.schools = None
        self.key = None

    def setData(self, arr):
        self.num = arr[0]
        self.street = arr[1]
        self.suffix = arr[2]
        self.key = self.num + ':' + self.street + ':' + map_suffix(self.suffix)
        
    def __repr__(self):
        return self.num + ':' + self.street + ':' + self.suffix


class AddressModel(db.Model):
    num = db.StringProperty(required=True)
    street = db.StringProperty(required=True)
    suffix = db.StringProperty(required=True)
    schools = db.StringListProperty(required=True)
    addrKey = db.StringProperty(required=True)

    def setData(self, arr):
        self.num = arr[0]
        self.street = arr[1]
        self.suffix = arr[2]
        self.addrKey = self.num + ':' + self.street + ':' + map_suffix(self.suffix)

    def __repr__(self):
        return self.num + ':' + self.street + ':' + self.suffix

class FetchHandler(webapp.RequestHandler):
    def get(self):
        self.response.headers['Content-Type'] = 'text/xml'
        
        model = {}
        if hasText(self.request.get('addresses')):
            path = os.path.join(os.path.dirname(__file__), 'fetch.htm')
            addrList = []
            for elem in self.request.get('addresses').split('|'):
                addr = Address()
                addr.setData(elem.split(':'))
                addrModel = db.GqlQuery('SELECT * FROM AddressModel WHERE addrKey = :1 LIMIT 1', addr.key).get()
                if addrModel:
                    logging.debug('address cached: %s' % addr)
                    addr.schools = addrModel.schools
                else:
                    url = toURL(addr)
                    logging.debug('address not cached: %s' % addr)
                    logging.debug('sending request to %s' % url)
                    addr.schools = parseSchoolFinderResult(urllib2.urlopen(url))
                    AddressModel(num=addr.num,
                                 street=addr.street,
                                 suffix=addr.suffix,
                                 schools=addr.schools,
                                 addrKey=addr.key).put()
                addrList.append(addr)
            self.response.out.write(template.render(path, {'addresses': addrList}))
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
        return ['NO MATCH FOUND']
    retval = []
    for school in soup.findAll('table')[0]('tr'):
        retval.append(parseSchool(school))
    return retval

def toURL(address):
    return 'http://search.lausd.k12.ca.us/cgi-bin/fccgi.exe?Direction=(none)&w3exec=schfinder2&Submit=Submit&StreetName=%s&StreetNumber=%s&Suffix=%s' % ( address.street, address.num, map_suffix(address.suffix) )

def hasText(str):
    """
    Returns True if the string argument is not empty.
    """
    return str != None and len(str.strip()) != 0

def main():
    logging.getLogger().setLevel(logging.DEBUG)
    urlmap = [
        # Maps /fetch.do -> FetchHandler
        ( '/fetch.do', FetchHandler ),
        # define additional mapping here
        ]
    application = webapp.WSGIApplication(urlmap, debug=True)
    run_wsgi_app(application)


if __name__ == '__main__':
    main()

