#!/usr/bin/python
#
# logs temperature from OWFS into postgres database
# (c) Tomasz Torcz, ISC License

import glob
import os

import psycopg2
import systemd.daemon
import time

sleep_seconds = 60 # make sure to be less than WatchdogSec=

systemd.daemon.notify("STATUS=Opening DB connection...")
try:
	dbconn = psycopg2.connect("dbname=temperature_log")
except Exception, e:
	print "Error connecting to DB, sorry: %s" % e
	exit(1)
dbconn.autocommit=True
cur = dbconn.cursor()
cur.execute("PREPARE put_temperature AS INSERT INTO temperatures (datetime, sensor_id, value) VALUES (NOW(), (SELECT id FROM sensors WHERE SN=$1), $2);")

systemd.daemon.notify("READY=1")
systemd.daemon.notify("STATUS=Entering main loop")
while True:
	for SN in glob.glob("/run/owfs/??.????????????"):
		systemd.daemon.notify("STATUS=Reading sensor %s..." % SN)
		temperature = open("%s/temperature" % SN).readline()
		# we won't be needing full path anymore, trim it
		SN = os.path.basename(SN)

		try:
			cur.execute("EXECUTE put_temperature (%s, %s);", (SN, temperature) )
		except psycopg2.IntegrityError:
			print "New sensor %s! Adding to database, please correct description." % SN
			cur.execute("INSERT INTO sensors (SN) VALUES (%s)", (SN,))
			cur.execute("EXECUTE put_temperature (%s, %s);", (SN, temperature) )

	systemd.daemon.notify("STATUS=Sleeping until %s" % time.ctime(time.time() + sleep_seconds))
	systemd.daemon.notify("WATCHDOG=1")
	time.sleep(sleep_seconds)

systemd.daemon.notify("STATUS=Cleaning up")
systemd.daemon.notify("STOPPING=1")
dbconn.close()
