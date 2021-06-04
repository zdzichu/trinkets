#!/usr/bin/python3

from flask import Flask, render_template
import datetime
import json
import os
import redis

DEBUG = os.getenv("DEBUG", False)
app = Flask(__name__)
app.config.from_object(__name__)

@app.route("/")
def main():
    hosts_drives = {}

    cache = redis.StrictRedis(host=os.getenv("R_HOST"), port=os.getenv("R_PORT"),
            charset="utf-8", decode_responses=True)

    for key in cache.keys("ssdead/*"):
        _, host, drive = key.split("/")

        smart_data = json.loads(cache.get(key))

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
                    percentage_used = 100 - int(attr["value"])
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

        if not host in hosts_drives:
            hosts_drives[host] = []

        hosts_drives[host].append({ "model_name": model_name,
            "drive": drive,
            "percentage_used": percentage_used,
            "dead_on": dead_time.strftime('%B %Y'),
            "temperature": temperature,
            "key_ttl": cache.ttl(key)
            })

    return render_template("main.html", hosts_drives=hosts_drives)

if __name__ == "__main__":
    app.run(host='::')


