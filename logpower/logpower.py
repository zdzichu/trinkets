#!/usr/bin/python3
#
# logs power meter outpu into postgres database
# (c) Tomasz Torcz, ISC License

from gpiozero import CPUTemperature

import os
import psycopg2
import re
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
raspi_serial = open('/sys/firmware/devicetree/base/serial-number', 'r').read().rstrip('\0')


# PREPARE DB QUERIES
# additionaly, store the temperature of raspberry CPU into
cur.execute("PREPARE put_temperature AS INSERT INTO temperatures (datetime, sensor_id, value) VALUES (NOW(), (SELECT id FROM sensors WHERE SN='{0}'), $1);".format(raspi_serial))
#
# cur.execute("PREPARE new_measurement AS INSERT INTO measurements (datetime) VALUES (NOW()) RETURNING id;")
# cur.execute("PREPARE put_measurement AS INSERT INTO power_measurements_items (pmi_measurement_id, pmi_group_a_medium, pmi_group_b_channel, pmi_group_c_type, pmi_group_c_type, pmi_group_d_variable, pmi_group_e_tariff, pmi_group_f_historical, pmi_data) VALUES($1, $2, $3, $4, $5, $6, $7, $8);")


# PREPARE REGEXPES
# adapted from https://github.com/openhab/openhab1-addons/blob/master/bundles/binding/org.openhab.binding.dsmr/src/main/java/org/openhab/binding/dsmr/internal/messages/OBISIdentifier.java#L23
obis_regexp = re.compile(
        "^((?P<group_a>\d)-(?P<group_b>\d{1,2}):)?"
        "(?P<group_c>\w{1,2})\.(?P<group_d>\w{1,2})"
        "(\.(?P<group_e>\d+)(\*(?P<group_f>\d{1,3}))?)?"
        "\((?P<data>.+)\)!?$" )

systemd.daemon.notify("READY=1")
systemd.daemon.notify("STATUS=Entering main loop")
while True:
	# open interface
	# try to read
	# read ok - start new measurement
        measurement_id = cur.execute("EXECUTE new_measurement")
        systemd.daemon.notify("STATUS=Processing measurement {0}".format(measurement_id)
	# loop - put values into table
	while readline:
		obis_match = obis_regexp.match(line)

		cur.execute("EXECUTE put_measurement ", measurement_id,
			obis_match.group("group_a"),
			obis_match.group("group_b"),
			obis_match.group("group_c"),
			obis_match.group("group_d"),
			obis_match.group("group_e"),
			obis_match.group("group_f"),
			obis_match.group("data"))


	# put the raspi temp, too
	cur.execute("EXECUTE put_temperature ({0});".format(CPUTemperature().temperature))

	dbconn.commit()
	systemd.daemon.notify("STATUS=Sleeping until %s" % time.ctime(time.time() + sleep_seconds))
	systemd.daemon.notify("WATCHDOG=1")
	time.sleep(sleep_seconds)

systemd.daemon.notify("STATUS=Cleaning up")
systemd.daemon.notify("STOPPING=1")
dbconn.close()
