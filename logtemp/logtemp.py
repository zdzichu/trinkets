#!/usr/bin/python3
#
# logs temperature from OWFS into postgres database
# (c) Tomasz Torcz, ISC License

import os
import psycopg2
import systemd.daemon
import time
from timeit import default_timer

from pyownet.protocol import proxy

sleep_seconds = int(os.getenv("WATCHDOG_USEC")) / (2*(10**6)) + 1

systemd.daemon.notify("STATUS=Opening owserver & DB connection...")
try:
	owproxy = proxy()
except Exception as err:
	print("Error connecting to owserver, sorry: {0}".format(err))
	exit(1)

try:
	dbconn = psycopg2.connect("dbname=house_metrics")
except Exception as err:
	print("Error connecting to DB, sorry: {0}".format(err))
	exit(2)

cur = dbconn.cursor()
cur.execute("PREPARE put_temperature AS INSERT INTO temperatures (datetime, sensor_id, value) VALUES (NOW(), (SELECT id FROM sensors WHERE SN=$1), $2);")

meter_cache = {}

systemd.daemon.notify("READY=1")
systemd.daemon.notify("STATUS=Entering main loop")
while True:
	# trigger temperature read
	owproxy.write('simultaneous/temperature', data=b'1')
	# readout takes about 750ms, sleep a bit
	time.sleep(1)

	nr_read = 0
	read_start = default_timer()
	for owitem in owproxy.dir(slash=False):
		if not owproxy.present("%s/temperature" % owitem):
			# not a temperature sensor, skip it
			continue

		SN = owitem[1:] # /slash be gone
		systemd.daemon.notify("STATUS=Reading sensor %s..." % SN)
		temperature = float(owproxy.read("%s/latesttemp" % owitem))
		nr_read += 1

		if temperature == 85.000:
			# magic value indicating sensor error, do not log it
			continue

		try:
			if temperature == meter_cache[SN]:
				# the same value as previous read, do not log
				continue
		except KeyError as e:
			# no data in cache, do nothing
			pass

		# update cache
		meter_cache[SN] = temperature

		try:
			cur.execute("EXECUTE put_temperature (%s, %s);", (SN, temperature) )
		except psycopg2.IntegrityError:
			print("New sensor {0}! Adding to database, please correct description.".format(SN) )
			dbconn.rollback()
			cur.execute("INSERT INTO sensors (SN) VALUES (%s)", (SN,) )
			dbconn.commit()
			cur.execute("EXECUTE put_temperature (%s, %s);", (SN, temperature) )

	read_end = default_timer()

	dbconn.commit()
	systemd.daemon.notify("STATUS=Read %d sensors in %.3f seconds. Sleeping until %s" % 
		(nr_read, read_end - read_start, time.ctime(time.time() + sleep_seconds)) )
	systemd.daemon.notify("WATCHDOG=1")
	time.sleep(sleep_seconds)

systemd.daemon.notify("STATUS=Cleaning up")
systemd.daemon.notify("STOPPING=1")
dbconn.close()
