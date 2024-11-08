#!/usr/bin/python
#
# Query a Candy appliance and publish status to MQTT
#

import datetime as dt
import json
import humanize
import logging
import os
import platform
import paho.mqtt.client as mqtt
import random
import time
import urllib.request
import itertools

candy_key = os.getenv("CANDY_KEY")
candy_host = os.getenv("CANDY_HOST")
mqtt_host = os.getenv("MQTT_HOST")
mqtt_user = os.getenv("MQTT_USER")
mqtt_password = os.getenv("MQTT_PASSWORD")
mqtt_topic = os.getenv("MQTT_TOPIC")

max_sleep_s = 3600
sleep_s = current_sleep_s = 45 + random.randrange(31)


def get_candy_json(host, key):
    candy_response = urllib.request.urlopen(f"http://{host}/http-read.json?encrypted=1").read().decode()
    logging.debug(f"Candy response raw: {candy_response}")

    candy_json = bytes.fromhex(candy_response).decode()
    # xor the json with the key
    candy_json = ''.join(chr(ord(c)^ord(k)) for c, k in zip(candy_json, itertools.cycle(key)))

    logging.debug(f"Candy response decrypted: {candy_json}")
    return json.loads(str(candy_json))


def nice_time(seconds):
    delta = dt.timedelta(seconds=seconds)
    return humanize.precisedelta(delta, minimum_unit='seconds')


logging.basicConfig(format='%(asctime)s %(levelname)s:%(message)s',
                    datefmt="%Y-%m-%dT%H:%M:%S%z",
                    level=logging.INFO)

logging.info(f"Connecting to MQTT broker {mqtt_host} as {mqtt_user}…")
mqttc = mqtt.Client(client_id=platform.node())
mqttc.username_pw_set(mqtt_user, password=mqtt_password)
mqttc.connect(mqtt_host)
mqttc.loop_start()

logging.info("Entering main loop…")
while True:
    try:
        candy_json = get_candy_json(candy_host, candy_key)
    except urllib.error.URLError as e:
        logging.debug(f"Connection to {candy_host} failed: {e}")
        # hack - send false report to indicate dyer is off
        mqtcc.publish("/agd/statusTD/StatoTD", 0)
        # hack2 - and pretend doors are open
        mqttc.publish("/agd/statusTD/DoorState", 0)
        mqttc.publish("/agd/statusTD/RemTime", 0)

        current_sleep_s = min(current_sleep_s * 2, max_sleep_s)
        logging.warning(f"Cannot get data, trying again in {nice_time(current_sleep_s)}")
        time.sleep(current_sleep_s)
        continue

    # at this point the readout must have been successful
    current_sleep_s = sleep_s   # reset sleep timer

    json_key = list(candy_json.keys())[0] # should discriminate type of hardware, e.g. 'statusTD' for tumble-dryer

    for status_item in candy_json[json_key]:
        status_value = candy_json[json_key][status_item]
        logging.debug(f"Publishing {mqtt_topic}/{json_key}/{status_item} = {status_value}")
        mqttc.publish(f"{mqtt_topic}/{json_key}/{status_item}", status_value)

    logging.info(f"Published OK, sleeping for {nice_time(sleep_s)}")
    time.sleep(sleep_s)

