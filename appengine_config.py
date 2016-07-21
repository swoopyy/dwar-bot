__author__ = 'denissamohvalov'

from google.appengine.ext import vendor
from google.appengine.api import urlfetch

vendor.add('lib')
urlfetch.set_default_fetch_deadline(60)
