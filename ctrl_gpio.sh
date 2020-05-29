#!/bin/bash

PIN=$1
VAL=$2

if [ -z "$PIN" -o -z "$VAL" ]
then 
	echo "paramters error"
	exit
fi

if [ ! -d "/sys/class/gpio/gpio${PIN}" ]
then
	echo $PIN > /sys/class/gpio/export
	echo "out" > /sys/class/gpio/gpio${PIN}/direction
fi

echo "$VAL" > /sys/class/gpio/gpio${PIN}/value
