# coding: utf-8

import webapp2
import urllib
import urllib2
import json
import logging
from google.appengine.api import users
import  telebot
from models import *

BOT_TOKEN = '267733776:AAEL8buwq4ZKAC7abvFw9sdhjKM4MV_shek'
BASE_URL = 'https://api.telegram.org/bot' + BOT_TOKEN + '/'

PLAYER_BASE_URL = 'https://w2.dwar.ru/user_info.php?nick='
FIGHT_BASE_URL = 'http://w2.dwar.ru/fight_info.php?fight_id='

tb = telebot.TeleBot(BOT_TOKEN)


class MainHandler(webapp2.RequestHandler):
    def get(self):
        tb.set_webhook(url="https://dwar-bot.appspot.com/webhooky")

class WebhookHandler(webapp2.RequestHandler):
    def post(self):
        self.response.write(self.request.body)




app = webapp2.WSGIApplication([
    ('/', MainHandler),
    ('/webhooky', WebhookHandler),
], debug=True)
