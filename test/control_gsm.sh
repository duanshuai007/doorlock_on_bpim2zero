#!/bin/bash


PIN=3

echo ${PIN} > /sys/class/gpio/export
echo out    > /sys/class/gpio/gpio${PIN}/direction

echo 0 > /sys/class/gpio/gpio${PIN}/value
sleep 2
echo 1 > /sys/class/gpio/gpio${PIN}/value
sleep 2
echo 0 > /sys/class/gpio/gpio${PIN}/value
sleep 2
echo 1 > /sys/class/gpio/gpio${PIN}/value

echo ${PIN} > /sys/class/gpio/unexport

echo "gsm module power reset done!"
