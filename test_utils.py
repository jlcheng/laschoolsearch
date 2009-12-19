import logging
import os
import re
import urllib2
import time


from google.appengine.ext import db
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext.webapp import template



class SleepHandler(webapp.RequestHandler):
    def get(self):
        self.response.headers['Content-Type'] = 'text/html'
        time.sleep(1)
        self.response.out.write('<?xml version="1.0"?><test>test</test>')

def main():
    urlmap = [
        # Maps /sleep.do -> Sleep
        ( '/sleep.do', SleepHandler ),
        # define additional mapping here
        ]
    application = webapp.WSGIApplication(urlmap, debug=True)
    run_wsgi_app(application)


if __name__ == '__main__':
    main()

