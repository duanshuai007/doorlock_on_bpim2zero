#!/bin/bash

mac=$(ifconfig  -a | grep HWaddr | grep eth0 | awk -F" " '{print $5}' | awk -F":" '{print $1$2$3$4$5$6}')
echo ${mac} > /tmp/eth0macaddr
