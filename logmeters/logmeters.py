#!/usr/bin/python

import logging
import json
import os
#import psycopg
#https://www.psycopg.org/psycopg3/docs/basic/usage.html
import systemd.daemon

# sql https://www.psycopg.org/psycopg3/docs/advanced/prepare.html

passed_fds = systemd.daemon.listen_fds()

if len(passed_fds) != 1:
    logging.error(f"Received {passed_fds} FDs from systemd, expected 1")
    exit(1)

print(f"Systemd gave us FDs {passed_fds}")
meter_pipe = os.fdopen(passed_fds[0], "r")

meter_cache = {}

systemd.daemon.notify("READY=1")

while meter_pipe:
    data = json.loads(meter_pipe.readline())
    #print(f"Got {json.dumps(data, indent=2)}")
    safe_serial = data.get('serial_number', '')

    try:
        if data['total_m3'] == meter_cache[data['id']]:
            # state did not change since last read
            print(f"New read of {safe_serial} ({data['id']}), but amount unchanged {data['total_m3']} m³")
            pass
        else:
            print(f"Storing new state of {safe_serial} ({data['id']}) as {data['total_m3']} m³")
            # store to db
            meter_cache[data['id']] = data['total_m3']

    except KeyError as e:
        # first read of this meter
        print(f"First read of {safe_serial} ({data['id']})")
        print(f"Storing first state of {safe_serial} ({data['id']}) as {data['total_m3']} m³")
        # storing…
        meter_cache[data['id']] = data['total_m3']

    print(meter_cache)

# nie wszystkie liczniki maja serial_number
# {"media":"cold water","meter":"mkradio3","name":"licznik44900252","id":"44900252","total_m3":76.9,"target_m3":76.9,"current_date":"2022-11-23T02:00:00Z","prev_date":"2021-12-31T02:00:00Z","timestamp":"2022-11-23T06:02:30Z","device":"rtlwmbus[not7cd]","rssi_dbm":19}

