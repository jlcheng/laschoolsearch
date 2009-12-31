import logging
import os
import re
import urllib2
from BeautifulSoup import BeautifulSoup


from google.appengine.ext import db
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext.webapp import template

class Address():
    def __init__(self):
        self.num = None
        self.street = None
        self.suffix = None
        self.schools = None
        self.success = None
        self.key = None

    def setData(self, arr):
        self.num = arr[0]
        self.street = arr[1]
        self.suffix = arr[2]
        self.key = self.num + ':' + self.street + ':' + self.suffix
        
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
        self.addrKey = self.num + ':' + self.street + ':' + self.suffix

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
                addr.success = False
                try:
                    addrModel = db.GqlQuery('SELECT * FROM AddressModel WHERE addrKey = :1 LIMIT 1', addr.key).get()
                    if addrModel:
                        logging.debug('address cached: %s' % addr)
                        addr.schools = addrModel.schools
                        addr.success = True
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
                        addr.success = True
                except Exception, e:
                    logging.error(e)
                    addr.schools = [repr(e)]
                addrList.append(addr)
            self.response.out.write(template.render(path, {'addresses': addrList}))
        else:
            path = os.path.join(os.path.dirname(__file__), 'fetch.htm')
            self.response.out.write(template.render(path, {}))

class ReverseGeoCodeHandler(webapp.RequestHandler):
    def get(self):
        longitude = self.request.get('longitude')
        latitude = self.request.get('latitude')
        path = os.path.join(os.path.dirname(__file__), 'fetch.htm')
        try:
            url = 'http://ws.geonames.org/findNearestAddress?lat=%s&lng=%s' % (longitude, latitude)
            logging.info(url);
            addr = parseGeonames(urllib2.urlopen(url))
            addrModel = db.GqlQuery('SELECT * FROM AddressModel WHERE addrKey = :1 LIMIT 1', addr.key).get()
            if addrModel:
                logging.debug('address cached: %s' % addr)
                addr.schools = addrModel.schools
                addr.success = True
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
                addr.success = True
            self.response.out.write(template.render(path, {'addresses': [addr]}))
        except Exception, e:
            logging.warn(e);
            addr = Address()
            addr.schools= ['Cannot lookup address for this location']
            addr.setData(('N/A','N/A','N/A'))
            self.response.out.write(template.render(path, {'addresses': [addr]}))
       

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

def parseGeonames(page):
    soup = BeautifulSoup(''.join(page.readlines()))
    addr = Address()
    addr.setData((soup.findAll('streetNumber')[0],
                  ' '.join(soup.findAll('street')[0][:-1]),
                  soup.findAll('street')[0][-1]))
    return addr

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
        ( '/reverse.do', ReverseGeoCodeHandler ),
        ]
    application = webapp.WSGIApplication(urlmap, debug=True)
    run_wsgi_app(application)


if __name__ == '__main__':
    main()

