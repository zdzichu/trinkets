#!/usr/bin/python3

from flask import Flask, render_template, request
import datetime
import json
import humanize
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

    for key in sorted(cache.keys("ssdead/*")):
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
            # in 1000s of 512 (sector size?)
            # https://www.percona.com/blog/2017/02/09/using-nvme-command-line-tools-to-check-nvme-flash-health/
            data_written = 1000 * int(smart_data["nvme_smart_health_information_log"]["data_units_written"]) * int(smart_data["logical_block_size"])

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
                    # Wear_Leveling_Count starts from 100 and goes down
                    # https://www.anandtech.com/show/8239/update-on-samsung-850-pro-endurance-vnand-die-size
                    percentage_used = 100 - int(attr["value"])

                elif attr["name"] == "Media_Wearout_Indicator":
                    # Media_Wearout_Indicator starts from 100 and goes down
                    # https://www.thomas-krenn.com/en/wiki/SMART_attributes_of_Intel_SSDs
                    percentage_used = 100 - int(attr["value"])

                # data written
                elif attr["name"] == "Total_LBAs_Written":
                    data_written = int(attr["raw"]["value"]) * int(smart_data["logical_block_size"])

                elif attr["name"] == "Host_Writes_32MiB":
                    data_written = int(attr["raw"]["value"]) * 32 * 1024*1024 # in bytes

                elif attr["name"] == "NAND_Writes_1GiB":
                    # https://www.intel.com/content/dam/www/public/us/en/documents/product-specifications/ssd-525-specification.pdf
                    data_written = int(attr["raw"]["value"]) * 1024*1024*1024 # get result in bytes

        else:
            print("wtf")

        # common fields
        power_on_hours  = int(smart_data["power_on_time"]["hours"])
        temperature = smart_data["temperature"]["current"]

        if percentage_used == 0:
            # super fresh, let's assume minimal usage
            percentage_used = 0.1

        percent_per_hour = percentage_used / power_on_hours
        percent_left = 100 - percentage_used
        hours_left = percent_left / percent_per_hour
        #print(f"drv {model_name} left pct {percent_left} left h {hours_left} pct-per-hour {percent_per_hour} uptime {power_on_hours} written {data_written} ")
        dead_time = datetime.datetime.now() + datetime.timedelta(hours=hours_left)

        if not host in hosts_drives:
            hosts_drives[host] = []

        hosts_drives[host].append({ "model_name": model_name,
            "drive": drive,
            "percentage_used": percentage_used,
            "dead_on": dead_time.strftime('%B %Y'),
            "written": humanize.naturalsize(data_written, binary=False),    # manufacturers use power-of-10 sizes
            "temperature": temperature,
            "key_ttl": cache.ttl(key),
            })

    return render_template("main.html", hosts_drives=hosts_drives, progress=request.args.get("progress"))

if __name__ == "__main__":
#    app.run(host='::', port=7770)
    app.run(host='::')


