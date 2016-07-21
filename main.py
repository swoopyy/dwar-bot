# coding: utf-8

import webapp2
import urllib
import urllib2
import json
import logging
from google.appengine.api import users
from models import *

BOT_TOKEN = '267733776:AAEL8buwq4ZKAC7abvFw9sdhjKM4MV_shek'
BASE_URL = 'https://api.telegram.org/bot' + BOT_TOKEN + '/'

PLAYER_BASE_URL = 'https://w2.dwar.ru/user_info.php?nick='
FIGHT_BASE_URL = 'http://w2.dwar.ru/fight_info.php?fight_id='

def check_admin():
    user = users.get_current_user()
    return user and users.is_current_user_admin()


class MeHandler(webapp2.RequestHandler):
    def get(self):
        if check_admin():
            self.response.write(json.dumps(json.load(urllib2.urlopen(BASE_URL + 'getMe'))))


class SetWebhookHandler(webapp2.RequestHandler):
    def get(self):
        url = self.request.get('url')
        logging.debug(check_admin())
        if url and check_admin():
            self.response.write(json.dumps(json.load(urllib2.urlopen(BASE_URL + 'setWebhook', urllib.urlencode({'url': url})))))


class GetUpdatesHandler(webapp2.RequestHandler):
    def get(self):
        self.response.write(json.dumps(json.load(urllib2.urlopen(BASE_URL + 'getUpdates'))))


class WebhookHandler(webapp2.RequestHandler):
    def post(self):
        body = json.loads(self.request.body)
        logging.info('request body:')
        logging.info(body)

        update_id = body['update_id']
        message = body['message']
        message_id = message.get('message_id')
        date = message.get('date')
        text = message.get('text')
        fr = message.get('from')
        chat = message['chat']
        chat_id = chat['id']

        if not text:
            logging.info('no text')
            return

        def reply(msg=None, *keyboard_buttons):
            if msg:
                url = urllib.urlencode({
                    'chat_id': str(chat_id),
                    'text': msg.encode('utf-8'),
                    'disable_web_page_preview': 'true',
                    'reply_to_message_id': str(message_id),
                    'reply_markup': {'keyboard': [{'text': txt} for txt in keyboard_buttons]}
                })
                logging.debug(url)
                resp = urllib2.urlopen(BASE_URL + 'sendMessage', url).read()
            else:
                logging.error('No message')
                resp = None

            logging.info('send response:')
            logging.info(resp)

        if text.startswith('/'):
            if text == '/start':
                reply(u'Здарова братан тут бот будит тибе маниторить нудистав и врагов.\n Все четка не валнуйся',
                      [u'Нудисты', u'Враги'])
                User.get_or_insert(str(chat_id)).put()
            elif text == '/stop':
                reply(u'Пака пидар')


        # CUSTOMIZE FROM HERE

        elif 'help' in text:
            reply('just continue in the format this is in....')

        else:
            logging.info('not enabled for chat_id {}'.format(chat_id))




app = webapp2.WSGIApplication([
    ('/me', MeHandler),
    ('/updates', GetUpdatesHandler),
    ('/set_webhook', SetWebhookHandler),
    ('/webhook', WebhookHandler),
], debug=True)
