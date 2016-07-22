# coding: utf-8

__author__ = 'denissamohvalov'
import urllib
import urllib2

def _get_fight_start_time(resp):
    time_marker = u'Начало боя:</span> <b class="redd">'.encode('utf8')
    begin = resp.find(time_marker) + len(time_marker) + 11
    end = begin + 5
    return resp[begin:end]

def _get_fight_name(resp):
    name_marker = u'Название:</span> <b class="redd">'.encode('utf8')
    begin = resp.find(name_marker) + len(name_marker)
    end = resp.find('</b>', begin)
    return resp[begin:end]

def _get_fight_id_from_resp(resp):
    fight_marker = 'fightId='
    begin = resp.find(fight_marker) + len(fight_marker)
    end = resp.find('&', begin)
    return resp[begin:end]

url = 'http://w2.dwar.ru/user_info.php?nick=bonay'
resp = urllib2.urlopen(url).read()

print(_get_fight_id_from_resp(resp))