#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# (c) Tomasz Torcz, ISC License
#
# needs python2-pyxdg.noarch python2-mechanize python2-html5lib

GRABLOG = "/home/zdzichu/.irssi/urllog"
OUTPAGE = "/var/www/pipebreaker.pl/z/urls.html"

import datetime
import os
import shelve
import time
import xdg.BaseDirectory

import sys
reload(sys)
sys.setdefaultencoding('utf8')

from mechanize import Browser

# great, simple script got caching support
# returns (is image, title)
def get_title(url, cache):

	got_image = False

	# najpierw w sposob młotkowy
	# nie trzeba sie łączyc, nie wpadnie na 403 albo robots.txt
	for ext in ("jpg", "jpeg", "gif", "png", "svg", ":large"):
		if url.lower().endswith(ext):
			got_image = True
			cache[url] = url
			continue

	if not cache.has_key(url):
		br = Browser()
		try:
			br.open(url)

			# teraz w sposób sprytny, bo facebook spierdolił linki do obrazków
			if br.response().info()["Content-type"] in ["image/png", "image/jpeg", "image/gif", "image/svg+xml"]:
				got_image = True
				cache[url] = url
			else:
				cache[url] = br.title()
		except Exception, e:
			print "Problem, Sir - '%s' - with %s" % (e, url)
			cache[url] = url
		br.close()

	return (got_image, cache[url])


# main() starts here

grablog = open(GRABLOG)

grabbed_urls = grablog.readlines()[-40:] # process last 40 links
grablog.close()

grabbed_urls.sort(reverse=True)

# title cache
cache_file = os.path.join(xdg.BaseDirectory.get_runtime_dir(), "urlgrab-cache")
cache = shelve.open(cache_file)

outfile = open(OUTPAGE, "w")

outfile.write("<!DOCTYPE html>\n")
outfile.write("<html><head><title>urlz for lulz: %s</title>\n" % datetime.datetime.now() )
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
			ago = "%d %s ago" % (count, period)
			break
		else:
			ago = "just now"

	outfile.write("<div>%s / <strong>%s</strong> %s &mdash; at %s\n" % (nick, channel, ago, time.ctime(int(timestamp)) ) )

	(got_image, title) = get_title(url, cache)

	# SFWize
	if url.startswith("http://media.oboobs.ru/"):
		got_image = False

	# hackize
	if url.startswith("https://fbcdn-sphotos-"):
		got_image = True

	if got_image:
		outfile.write("</div>\n %s<br/> \n<img src='%s'>" % (url, url) )
	else:
		outfile.write("<h4><a href='%s'> → %s ←</a> <br/>\n%s </h4>\n</div>\n" % (url, title, ("" if title == url else url) ))

	outfile.write(" <hr/>\n\n")

outfile.write("</body></html>")

outfile.close();

cache.close()

print "Links made"
