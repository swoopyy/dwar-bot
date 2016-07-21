__author__ = 'denissamohvalov'
from google.appengine.ext import ndb


class Victim(ndb.Model):
    link = ndb.StringProperty(required=True)
    is_online = ndb.BooleanProperty()
    is_fighting = ndb.BooleanProperty


class User(ndb.Model):
    chat_id = ndb.StringProperty(required=True)
    victims = ndb.KeyProperty(kind=Victim, repeated=True)
    wants_receive_nudists = ndb.BooleanProperty()

