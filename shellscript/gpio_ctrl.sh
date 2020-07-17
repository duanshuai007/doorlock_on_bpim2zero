#!/bin/bash

no=$1
val=$2

echo ${no}	> /sys/class/gpio/export
echo out	> /sys/class/gpio/gpio${no}/direction
echo ${val} > /sys/class/gpio/gpio${no}/value

echo ${no}	> /sys/class/gpio/unexport
