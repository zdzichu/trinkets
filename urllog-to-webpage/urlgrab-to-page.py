#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# (c) Tomasz Torcz, ISC License
#
# needs python3-pyxdg.noarch python3-mechanize python3-html5lib

GRABLOG = "/home/zdzichu/.irssi/urllog"
OUTPAGE = "/var/www/pipebreaker.pl/z/urls.html"

import codecs
import datetime
import os
import pickle
import time
import xdg.BaseDirectory

#import sys
#reload(sys)
#sys.setdefaultencoding('utf8')

from mechanize import Browser

class URLCache:
	'''Simple caching object.
	   get, put, explicit close'''
	cache = None

class ShelveCache(URLCache):
	'''Implement cache mechanism using shelve'''
	def __init__(self):
		import shelve
		cache_file = os.path.join(xdg.BaseDirectory.get_runtime_dir(), "urlgrab-cache")
		self.cache = shelve.open(cache_file)

	def __del__(self):
		self.cache.close()

	def put(self, key, value):
		self.cache[str(key)] = value

	def get(self, key):
		try:
			return self.cache[str(key)]
		except KeyError as error:
			return None


class RedisCache(URLCache):
	'''Store stuff one remote redis'''
	def __init__(self):
		import redis

		self.cache = redis.StrictRedis(host='redis-urlcache.tau.pipebreaker.pl')

	def put(self, key, value):
		self.cache.set(key, pickle.dumps(value))
		self.cache.expire(key, datetime.timedelta(weeks=20))

	def get(self, key):
		return pickle.loads(self.cache.get(key))


# great, simple script got caching support
# returns (is image, title)
def get_title(url):

	# najpierw w sposob młotkowy
	# nie trzeba sie łączyc, nie wpadnie na 403 albo robots.txt
	for ext in ("jpg", "jpeg", "gif", "png", "svg", ":large"):
		if url.lower().endswith(ext):
			cache.put(url, (url, True))
			continue

	try:
		(title, got_image) = cache.get(url)

	except TypeError:
		# got None, key not in cache - open and get the title
		br = Browser()
		try:
			br.open(url)

			# teraz w sposób sprytny, bo facebook spierdolił linki do obrazków
			if br.response().info()["Content-type"] in ["image/png", "image/jpeg", "image/gif", "image/svg+xml"]:
				cache.put(url, (url, True))
			else:
				cache.put(url, (br.title(), False))
		except Exception as exception:
			print(f"Problem, Sir - {exception} - with {url}")
			cache.put(url, (url, False))
		br.close()

	# try again
	(title, got_image) = cache.get(url)

	return (got_image, title)


# main() starts here

grablog = codecs.open(GRABLOG, 'r', encoding="utf-8")

grabbed_urls = grablog.readlines()[-40:] # process last 40 links
grablog.close()

grabbed_urls.sort(reverse=True)

# title cache
#cache = ShelveCache()
cache = RedisCache()

outfile = codecs.open(OUTPAGE, "w", encoding="utf-8")

outfile.write("<!DOCTYPE html>\n")
outfile.write("<html><head><title>urlz for lulz: %s</title>\n" % datetime.datetime.now().astimezone().isoformat(timespec='minutes') )
outfile.write("<meta charset='utf-8'><meta http-equiv='refresh' content='300' ></head>\n")
outfile.write("<body style=\"font-family: Cantarell\">\n")

for line in grabbed_urls:
	(timestamp, nick, channel, url) = line.split(" ")

	url = url.rstrip()

	timedelta = datetime.timedelta(seconds=time.time() - int(timestamp))
	days, seconds = timedelta.days, timedelta.seconds
	hours = seconds // 3600
	minutes = (seconds % 3600) // 60
	seconds = (seconds % 60)

	for period in ("days", "hours", "minutes", "seconds"):
		count = locals()[period]
		if count > 0:
			if count == 1:
				# strip plural 's'
				period = period[:-1]
			ago = "%d %s ago" % (count, period)
			break
		else:
			ago = "just now"

	outfile.write("<div>%s / <strong>%s</strong> %s &mdash; at %s %s\n" % (nick, channel, ago, time.ctime(int(timestamp)), time.strftime("%Z") ) )

	if days == 0 and hours < 8:
		# prefetch today's links
		outfile.write("<link rel='prefetch' href='%s'/>\n" % url)

	(got_image, title) = get_title(url)

	# SFWize
	if url.startswith("http://media.oboobs.ru/"):
		got_image = False

	# hackize
	if url.startswith("https://fbcdn-sphotos-"):
		got_image = True

	if got_image:
		outfile.write("</div>\n %s<br/> \n<img src='%s'>" % (url, url) )
	else:
		outfile.write(u"<h4><a href='%s'> → %s ←</a> <br/>\n%s </h4>\n</div>\n" % (url, title, ("" if title == url else url) ))

	outfile.write(" <hr/>\n\n")

outfile.write("</body></html>")

outfile.close();

print("Links made")
