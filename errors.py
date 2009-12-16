import os

from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext.webapp import template

class NotFound(webapp.RequestHandler):
    def get(self):
      path = os.path.join(os.path.dirname(__file__), 'error.htm')
      self.response.set_status(404)
      self.response.headers['Content-Type'] = 'text/html'
      self.response.out.write(template.render(path, {}))

def main():
    urlmap = [
        # All -> NotFound
        ( '/.*', NotFound ),
        # define additional mapping here
        ]
    application = webapp.WSGIApplication(urlmap, debug=True)
    run_wsgi_app(application)

if __name__ == '__main__':
    main()
