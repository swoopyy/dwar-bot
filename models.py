__author__ = 'denissamohvalov'
from google.appengine.ext import ndb


class Enemy(ndb.Model):
    name = ndb.StringProperty()
    link = ndb.StringProperty()
    is_online = ndb.BooleanProperty(default=False)
    is_nudist = ndb.BooleanProperty(default=False)


class User(ndb.Model):
    enemies = ndb.KeyProperty(Enemy, repeated=True)
    wants_receive_nudists = ndb.BooleanProperty(default=False)
    state = ndb.IntegerProperty()

