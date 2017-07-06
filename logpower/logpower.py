#!/usr/bin/python3
#
# logs power meter outpu into postgres database
# (c) Tomasz Torcz, ISC License

from gpiozero import CPUTemperature

import os
import psycopg2
import systemd.daemon
import time


sleep_seconds = int(os.getenv("WATCHDOG_USEC")) / (2*(10**6)) + 1

systemd.daemon.notify("STATUS=Opening DB connection...")
try:
	dbconn = psycopg2.connect("dbname=house_metrics")
except Exception as err:
	print("Error connecting to DB, sorry: {0}".format(err))
	exit(1)
cur = dbconn.cursor()


# we are running on Raspi, get the serial number
raspi_serial = "grep /proc/cpuinfo"


# additionaly, store the temperature of raspberry CPU into
cur.execute("PREPARE put_temperature AS INSERT INTO temperatures (datetime, sensor_id, value) VALUES (NOW(), (SELECT id FROM sensors WHERE SN={0}), $1);".format(raspi_serial))
#
# cur.execute("PREPARE new_measurement AS INSERT INTO measurements (datetime) VALUES (NOW()) RETURNING id;")
# cur.execute("PREPARE put_measurement AS INSERT INTO power_measurements_items (pmi_measurement_id, pmi_group_a_medium, pmi_group_b_channel, pmi_group_c_type, pmi_group_c_type, pmi_group_d_variable, pmi_group_e_tariff, pmi_group_f_historical, pmi_data) VALUES($1, $2, $3, $4, $5, $6, $7, $8);")


systemd.daemon.notify("READY=1")
systemd.daemon.notify("STATUS=Entering main loop")
while True:
	# open interface
	# try to read
#	systemd.daemon.notify("STATUS=Reading sensor %s..." % SN)
	# read ok - start new measurement
	# loop - put values into table

	# put the raspi temp, too
	temperature = CPUTemperature()
	cur.execute("EXECUTE put_temperature ({0});".format(temperature))

	dbconn.commit()
	systemd.daemon.notify("STATUS=Sleeping until %s" % time.ctime(time.time() + sleep_seconds))
	systemd.daemon.notify("WATCHDOG=1")
	time.sleep(sleep_seconds)

systemd.daemon.notify("STATUS=Cleaning up")
systemd.daemon.notify("STOPPING=1")
dbconn.close()
