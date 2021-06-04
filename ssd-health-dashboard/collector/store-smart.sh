#!/bin/bash

R_TTL=$((7*24*3600))

HOST=$(hostname --fqdn)

for drive in /dev/sd? /dev/nvme?; do
	[ -e $drive ] || continue
	R_KEY="ssdead/${HOST}/$(basename $drive)"
	echo Storing $R_KEY
	smartctl --all --json=c $drive | \
		redis-cli -h $R_HOST -p $R_PORT -x set $R_KEY
	redis-cli -h $R_HOST -p $R_PORT expire $R_KEY $R_TTL
done
