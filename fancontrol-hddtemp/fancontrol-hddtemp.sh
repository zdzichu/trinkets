#!/bin/bash
#
# 30 - 42 -> 20 to 255
# 38 -> 160

DELAY=30
DRIVES="ata-WDC_WD60EFRX-68MYMN0_WD-WX31D3408062 ata-WDC_WD60EFRX-68MYMN0_WD-WX31D3408253 ata-Samsung_SSD_850_PRO_256GB_S39KNX0J236503V"
DRIVE_FAN="/sys/devices/platform/it87.2608/hwmon/hwmon1/pwm2"
MIN_PWM=20
STEP_PWM=20

systemd-notify --ready

echo "Controlling ${DRIVE_FAN}, every ${DELAY} seconds"
echo "Drives: ${DRIVES}"

while true; do
	MAX_TEMP=30
	# get temperatures
	for drive in $DRIVES; do
		temp=$(/usr/sbin/hddtemp -n /dev/disk/by-id/${drive})
	#	echo MAX: $MAX_TEMP, temp: $temp
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

