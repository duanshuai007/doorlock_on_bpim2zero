#!/bin/bash

while true
do
	temp=$(cat /sys/class/thermal/thermal_zone0/temp)
	temp=$(expr ${temp} / 1000)
	echo ${temp}
	sleep 5
done
