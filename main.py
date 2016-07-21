# coding: utf-8

import webapp2
import urllib
import urllib2
import json
import logging
from google.appengine.api import users, memcache
from google.appengine.ext.deferred import deferred
from models import *

BOT_TOKEN = '267733776:AAEL8buwq4ZKAC7abvFw9sdhjKM4MV_shek'
BASE_URL = 'https://api.telegram.org/bot' + BOT_TOKEN + '/'

PLAYER_BASE_URL = 'https://w2.dwar.ru/user_info.php?nick='
FIGHT_BASE_URL = 'http://w2.dwar.ru/fight_info.php?fight_id='

MAX_NUMBER_OF_ENEMIES = 3

NONE_STATE = 0
ADD_ENEMY_STATE = 1
REMOVE_ENEMY_STATE = 2

def check_admin():
    user = users.get_current_user()
    return user and users.is_current_user_admin()


class MeHandler(webapp2.RequestHandler):
    def get(self):
        self.response.write(json.dumps(json.load(urllib2.urlopen(BASE_URL + 'getMe'))))


class SetWebhookHandler(webapp2.RequestHandler):
    def get(self):
        url = self.request.get('url')
        logging.debug(check_admin())
        self.response.write(json.dumps(json.load(urllib2.urlopen(BASE_URL + 'setWebhook', urllib.urlencode({'url': url})))))


class GetUpdatesHandler(webapp2.RequestHandler):
    def get(self):
        self.response.write(json.dumps(json.load(urllib2.urlopen(BASE_URL + 'getUpdates'))))


class OnlineCheckHandler(webapp2.RequestHandler):
    def get(self):
        pass


def reply(chat_id, message_id, msg=None, parse_mode=None, *keyboard_buttons):
    if msg:
        dct = {
            'chat_id': str(chat_id),
            'text': msg,
            'disable_web_page_preview': 'true',
            #'reply_to_message_id': str(message_id),
        }
        if parse_mode:
            dct['parse_mode'] = parse_mode

        if keyboard_buttons:
            dct['reply_markup'] = json.dumps({'keyboard': [[{'text': txt} for txt in keyboard_buttons]]})
        else:
            dct['reply_markup'] = json.dumps({'hide_keyboard': True})
        _data = {}
        for k, v in dct.iteritems():
            _data[k] = unicode(v).encode('utf-8')
        logging.debug(json.dumps(_data))
        url = urllib.urlencode(_data)
        logging.debug(url)
        resp = urllib2.urlopen(BASE_URL + 'sendMessage', url).read()
    else:
        logging.error('No message')
        resp = None

    logging.info('send response:')
    logging.info(resp)


def collect_enemy_info(chat_id, message_id, is_nudist, *enemies):
    msg = u"Вот сматри:\n"
    number = 1
    for enemy in enemies:
        msg += str(number) + ('. <a href="%s">%s</a> ' % (enemy['link'], enemy['name']))
        url = enemy['link']
        resp = urllib2.urlopen(url).read()
        msg += " Online " if _get_online_from_resp(resp) else " Offline "
        msg += _get_location_from_resp(resp) + "\n"
        number += 1
    if is_nudist:
        reply(chat_id, message_id, msg, 'HTML', *[u'Отписаться', u'Вывести нудистов', u'Назад'])
    else:
        reply(chat_id, message_id, msg, 'HTML', *[u'Мои враги', u'Добавить врага', u'Удалить врага', u'Назад'])



def _get_location_from_resp(resp):
    begin = resp.find('Location=') + 9
    end = resp.find('&', begin)
    return urllib.unquote(resp[begin:end].replace('+', ' ')).decode('utf8')


def _get_online_from_resp(resp):
    index = resp.find('online=')
    return resp[index + 7] == '1'


def _set_enemy_link_and_online(resp, enemy):
    index = resp.find('&noredir=')
    if index == -1 and resp.find('avatar_picture') != -1:
        return False
    if index != -1:
        end = resp.find("';", index)
        enemy.link = PLAYER_BASE_URL + urllib.quote_plus(enemy.name.encode('utf-8')) + "&noredir=" + resp[index+9:end]
    else:
        enemy.link = PLAYER_BASE_URL + urllib.quote_plus(enemy.name.encode('utf-8'))
    return True

def add_enemy(user, enemy_nick):
    url = PLAYER_BASE_URL + urllib.quote_plus(enemy_nick.encode('utf-8'))
    resp = urllib.urlopen(url).read()
    if u'Пользователь не найден!'.encode('utf8') in resp:
        reply(user.key.id(), None, u'Братка ты ввел ниверныи ник', None, *[u'Мои враги', u'Добавить врага', u'Удалить врага', u'Назад'])
    else:
        enemy = Enemy.get_or_insert(enemy_nick)
        enemy.name = enemy_nick

        if not _set_enemy_link_and_online(resp, enemy):
            reply(user.key.id(), None, u'Братка у тваево врага закрытая инфа', None, *[u'Мои враги', u'Добавить врага', u'Удалить врага', u'Назад'])
            return

        user.enemies.append(
            enemy.put()
        )
        reply(user.key.id(), None, u'Братка враг добавлен', None, *[u'Мои враги', u'Добавить врага', u'Удалить врага', u'Назад'])
    user.state = NONE_STATE
    user.put()

def remove_enemy(user, enemy_nick):
    for i in range(len(user.enemies)):
        if user.enemies[i].get().name.encode('utf8') == enemy_nick.encode('utf8'):
            user.enemies.remove(user.enemies[i])
            reply(user.key.id(), None, u'Враг удален', None, *[u'Мои враги', u'Добавить врага', u'Удалить врага', u'Назад'])
            user.state = NONE_STATE
            user.put()
            return
    reply(user.key.id(), None, u'Враг не найден', None, *[u'Мои враги', u'Добавить врага', u'Удалить врага', u'Назад'])
    user.state = NONE_STATE
    user.put()


class WebhookHandler(webapp2.RequestHandler):

    def post(self):
        body = json.loads(self.request.body)
        logging.info('request body:')
        logging.info(body)

        message = body['message']
        message_id = message.get('message_id')
        text = message.get('text')
        chat = message['chat']
        chat_id = chat['id']

        if not text:
            return

        if text.startswith('/'):
            if text == '/start':
                reply(chat_id, message_id, u'Здарова братан тут бот будит тибе маниторить нудистав и врагов. Все четка',
                      None,
                      *[u'Нудисты', u'Враги'])
                User.get_or_insert(str(chat_id)).put()
            return

        user = User.get_by_id(str(chat_id))
        if text == u'Нудисты':
            if user.wants_receive_nudists:
                reply(chat_id, message_id, u'Отпишись от получения инфы о нудистах если хочещ брат.', None, *[u'Отписаться', u'Вывести нудистов', u'Назад'])
            else:
                reply(chat_id, message_id, u'Подпишись на палучения инфы о нудистах брат. Буду слать тибе'
                      u'инфу кагда нудист зашол где и кагда начел бой.', None, *[u'Подписаться', u'Вывести нудистов', u'Назад'])

        elif text == u'Отписаться':
            user.wants_receive_nudists = False
            future = user.put_async()
            reply(chat_id, message_id, u'Ок', None, *[u'Нудисты', u'Враги'])
            future.get_result()

        elif text == u'Подписаться':
            user.wants_receive_nudists = True
            future = user.put_async()
            reply(chat_id, message_id, u'Ок', None, *[u'Нудисты', u'Враги'])
            future.get_result()

        elif text == u'Враги':
            txt = u'Всех твоих врагов я буду чекать  и присылать тебе ' \
                  u'софбщение если эти клоуны зашли в игру по сваей дерзасти'
            reply(chat_id, message_id, txt, None, *[u'Мои враги', u'Добавить врага', u'Удалить врага', u'Назад'])

        elif text == u'Мои враги':
            enemies = None #memcache.get('enemies' + user.key.id())
            if enemies:
                deferred.defer(collect_enemy_info, chat_id, message_id, False, *enemies)
            else:
                enemies = []
                for enemy in user.enemies:
                    enemies.append(
                        {
                            'name': enemy.get().name,
                            'link': enemy.get().link,
                        }
                    )
                memcache.set('enemies' + user.key.id(), enemies)
                deferred.defer(collect_enemy_info, chat_id, message_id, False, *enemies)

        elif text == u'Добавить врага':
            if len(user.enemies) == MAX_NUMBER_OF_ENEMIES:
                reply(chat_id, message_id, u'Сори братан но больше 3 врагов не магу', None,
                      *[u'Мои враги', u'Добавить врага', u'Удалить врага', u'Назад'])
                return
            user.state = ADD_ENEMY_STATE
            future = user.put_async()
            reply(chat_id, message_id, u'Пришли мне ник своево врага братка', None)
            future.get_result()

        elif text == u'Удалить врага':
            user.state = REMOVE_ENEMY_STATE
            future = user.put_async()
            reply(chat_id, message_id, u'Пришли ник врага каво удалить', None)
            future.get_result()

        elif text == u'Назад':
             reply(chat_id, message_id, u'Гари потер царь',
                      None,
                      *[u'Нудисты', u'Враги'])

        elif text == u'Вывести нудистов':
            nudists = memcache.get('nudists')
            if nudists:
                deferred.defer(collect_enemy_info, chat_id, message_id, True, *nudists)
            else:
                query = Enemy.query(Enemy.is_nudist == True)
                nudists = []
                for nudist in query.fetch():
                    logging.debug(str(nudist))
                    nudists.append(
                        {
                            'name': nudist.name,
                            'link': nudist.link,
                        }
                    )
                memcache.set('nudist' + user.key.id(), nudists)
                deferred.defer(collect_enemy_info, chat_id, message_id, True, *nudists)

        elif user.state == ADD_ENEMY_STATE:
            logging.info("User %s just added enemy %s" % (user.key.id(), text))
            memcache.set('enemies' + user.key.id(), None)
            deferred.defer(add_enemy, user, text)

        elif user.state == REMOVE_ENEMY_STATE:
            logging.info("User %s just removed enemy %s" % (user.key.id(), text))
            memcache.set('enemies' + user.key.id(), None)
            deferred.defer(remove_enemy, user, text)


app = webapp2.WSGIApplication([
    ('/me', MeHandler),
    ('/updates', GetUpdatesHandler),
    ('/set_webhook', SetWebhookHandler),
    ('/webhook', WebhookHandler),
    ('/cron/online', OnlineCheckHandler),
], debug=True)
