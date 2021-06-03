#!/usr/bin/python

import datetime
import json
import os
import redis


cache = redis.StrictRedis(host=os.getenv("R_HOST"), port=os.getenv("R_PORT"), charset="utf-8", decode_responses=True)

for key in cache.keys("ssdead/*"):
    _, host, drive = key.split("/")

    #print(key)
    smart_data = json.loads(cache.get(key))
    key_ttl = cache.ttl(key)

    if not "model_name" in  smart_data:
        # not a proper smartctl dump, skip
        continue
    else:
        model_name = smart_data["model_name"]

    if "nvme_smart_health_information_log" in smart_data:
        # looks like nvme
        percentage_used = int(smart_data["nvme_smart_health_information_log"]["percentage_used"])

    elif "ata_smart_attributes" in smart_data:
        # SATA SSD, I suppose
        try:
            if smart_data["rotation_rate"] != 0:
                # not a SSD, skip
                continue
        except KeyError:
                # probably not a SSD
                continue

        for attr in smart_data["ata_smart_attributes"]["table"]:
            if attr["name"] == "Wear_Leveling_Count":
                percentage_used = int(attr["value"])
            elif attr["name"] == "Workld_Media_Wear_Indic":
                # this is for intel, but maybe look at Media_Wearout_Indicator ?
                percentage_used = int(attr["value"]) / 1024
    else:
        print("wtf")

    # common fields
    power_on_hours  = int(smart_data["power_on_time"]["hours"])
    temperature = smart_data["temperature"]["current"]

    if percentage_used == 0:
        # super fresh, let's assume minimal usage
        percentage_used = 0.1

    percent_per_hour = power_on_hours / percentage_used
    percent_left = 100 - percentage_used
    hours_left = percent_left * percent_per_hour

    dead_time = datetime.datetime.now() + datetime.timedelta(hours=hours_left)

    print(f"{host}\t\t{model_name} ({drive}, 🌡️ {temperature}°C):\tused {percentage_used}%, dead on 😵 {dead_time.strftime('%B %Y')}; key expires in {key_ttl/3600:.0f}h ")

