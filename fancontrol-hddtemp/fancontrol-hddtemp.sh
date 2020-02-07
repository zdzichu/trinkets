#!/bin/bash
#
# 30 - 42 -> 20 to 255
# 38 -> 160

DELAY=30
DRIVES_NAMES="ata-WDC_WD60EFRX-68MYMN0_WD-WX31D3408062 ata-WDC_WD60EFRX-68MYMN0_WD-WX31D3408253 ata-Samsung_SSD_850_PRO_256GB_S39KNX0J236503V"
DRIVE_FAN="/sys/devices/platform/it87.2608/hwmon/[[:print:]]*/pwm2"
MIN_PWM=20
STEP_PWM=20

# figure sensors names from drive names
# udevadm returns something along:
# /devices/pci0000:00/0000:00:1f.2/ata2/host1/target1:0:0/1:0:0:0/block/sdb
for drive in $DRIVES_NAMES; do
# get the DEVPATH, trim beginning of line, replace colons by minuses, leave ony first two
	SCSI_TARGET_CHANNEL=$(udevadm info /dev/disk/by-id/${drive} | \
	grep DEVPATH= | \
	sed s/^.*target// | \
	tr : - | \
	cut --delimiter - --fields 1,2 )

	DRIVES="${DRIVES} drivetemp-scsi-${SCSI_TARGET_CHANNEL}"
done


systemd-notify --ready

echo "Controlling ${DRIVE_FAN}, every ${DELAY} seconds"
echo "Drives: ${DRIVES_NAMES}" 

while true; do
	MAX_TEMP=30
	# get temperatures
	for drive in $DRIVES; do
		# output is  temp1_input: 36.000
		# we need only decimal degrees (that's the resolution of SSD's sensor)
		# NOTE: maybe investigate sensor's JSON output and jq
		temp=$(/usr/bin/sensors --no-adapter -u ${drive} | grep _input | cut --delimiter : --fields 2 | cut --delimiter . --fields 1 )
		#echo MAX: $MAX_TEMP, temp: $temp
		MAX_TEMP=$(( MAX_TEMP > temp ? MAX_TEMP : temp))
	done
	#echo new MAX: $MAX_TEMP

	VAR_PWM=$(( MAX_TEMP - 30  ))
	VAR_PWM=$(( VAR_PWM < 0 ? 0 : VAR_PWM))

	FINAL_PWM=$(( MIN_PWM + VAR_PWM * STEP_PWM))
	FINAL_PWM=$(( FINAL_PWM > 255 ? 255 : FINAL_PWM))

	systemd-notify --status="Max HDD temp $MAX_TEMP, set spin PWM to $FINAL_PWM"

	# manual PWM control
	echo 1 > ${DRIVE_FAN}_enable
	echo ${FINAL_PWM} > ${DRIVE_FAN}

	sleep $DELAY
done

