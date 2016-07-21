__author__ = 'denissamohvalov'
import urllib
import urllib2
url = 'https://w1.dwar.ru/user_info.php?nick=dkoka'
print('fightId' in urllib2.urlopen(url).read())