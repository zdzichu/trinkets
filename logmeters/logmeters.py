#!/usr/bin/python

import logging
import json
import os
import systemd.daemon

# sql https://www.psycopg.org/psycopg3/docs/advanced/prepare.html

passed_fds = systemd.daemon.listen_fds()

if len(passed_fds) != 1:
    logging.error(f"Received {passed_fds} FDs from systemd, expected 1")
    exit(1)

logging.info(f"Systemd gave us {passed_fds}")
meter_pipe = os.fdopen(passed_fds[0], "r")

meter_cache = {}

systemd.daemon.notify("READY=1")

while meter_pipe:
    data = json.loads(meter_pipe.readline())
    #print(f"Got {json.dumps(data, indent=2)}")
    try:
        if data['total_m3'] == meter_cache[data['serial_number']]:
            # state did not change since last read
            pass
        else:
            print("Storing state of {data['serial_number']} as {data['total_m3']} m³")

    except KeyError as e:
        # first read of this meter
        print(f"First read of {data['serial_number']}")
        print(f"Storing state of {data['serial_number']} as {data['total_m3']} m³")
        # storing…
        meter_cache[data['serial_number']] = data['total_m3']


