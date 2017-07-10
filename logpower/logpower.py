#!/usr/bin/python3
#
# logs power meter outpu into postgres database
# (c) Tomasz Torcz, ISC License

from gpiozero import CPUTemperature

# use my hacked up version
from iec62056.client import Client

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
cur.execute("PREPARE new_measurement AS INSERT INTO measurements (m_datetime) VALUES (NOW()) RETURNING m_id;")
cur.execute("PREPARE put_measurement AS INSERT INTO power_measurements_items (pmi_measurement_id, pmi_group_a_medium, pmi_group_b_channel, pmi_group_c_type, pmi_group_d_variable, pmi_group_e_tariff, pmi_group_f_historical, pmi_data) VALUES($1, $2, $3, $4, $5, $6, $7, $8);")


# PREPARE REGEXPES
# adapted from https://github.com/openhab/openhab1-addons/blob/master/bundles/binding/org.openhab.binding.dsmr/src/main/java/org/openhab/binding/dsmr/internal/messages/OBISIdentifier.java#L23
obis_regexp = re.compile(
	"^((?P<group_a>\d)-(?P<group_b>\d{1,2}):)?"       # 1-2:   - optional group of digit + 1 or 2 digits
	"(?P<group_c>\w{1,2})\.(?P<group_d>\w{1,2})"      # 3.4    - required group of 1 or 2 alphanumerics + 1 or 2 alphanumeric
	"(\.(?P<group_e>\d{1,2})(\*(?P<group_f>\d{1,3}))?)?"  # .5*6   - optional group of 1 or 2 digits + optional 1 to 3 digits
	"\((?P<data>.+)\)!?$" )                           # ( )    - required group of data in parens, with optional exclamation mark

# open serial interface for IEC62056-21
client = Client(port='/dev/ttyUSB0')
comm_end = b'\x03'

systemd.daemon.notify("READY=1")
systemd.daemon.notify("STATUS=Entering main loop")
while True:
	with client.serial_connection():
		client._send_sign_on()
		client._read_identification()
		client._send_ack_with_options()

		# read ok - start new measurement
		cur.execute("EXECUTE new_measurement")
		measurement_id = cur.fetchone()[0]
		systemd.daemon.notify("STATUS=Processing measurement {0}".format(measurement_id))

		# read the meter in loop
		readout_start = time.time()
		while True:
			binary_line = client.ser.readline()
			line = binary_line.decode('ascii').replace('\r\n', '')

			if comm_end in binary_line:
				# end of line detected
				break

			obis_match = obis_regexp.match(line)
			if obis_match is None:
				print("Cannot parse: {0}".format(line)
				continue
			#print("{0} → {1}".format(line, obis_match.groups()))
			cur.execute("EXECUTE put_measurement (%s, %s, %s, %s, %s, %s, %s, %s); ",
				(measurement_id,
				obis_match.group("group_a"),
				obis_match.group("group_b"),
				obis_match.group("group_c"),
				obis_match.group("group_d"),
				obis_match.group("group_e"),
				obis_match.group("group_f"),
				obis_match.group("data") ) )

		# out of loop - everything read
	readout_length = time.time() - readout_start

	# put the raspi temp, too
	cur.execute("EXECUTE put_temperature ({0});".format(CPUTemperature().temperature))

	dbconn.commit()
	if readout_length > sleep_seconds / 2:
		print("Meter readout took %.2f second, while watchdog is about %ds." % (readout_length, sleep_seconds * 2))
	systemd.daemon.notify("STATUS=Sleeping until %s" % time.ctime(time.time() + sleep_seconds))
	systemd.daemon.notify("WATCHDOG=1")
	time.sleep(sleep_seconds)

systemd.daemon.notify("STATUS=Cleaning up")
systemd.daemon.notify("STOPPING=1")
dbconn.close()
