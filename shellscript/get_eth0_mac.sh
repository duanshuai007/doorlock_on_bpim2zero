#!/bin/bash

mac=$(ifconfig eth0 | grep HWaddr | awk -F" " '{print $5}' | awk -F":" '{print $1$2$3$4$5$6}')
echo ${mac} > /tmp/eth0macaddr
/bin/hostname zywldl${mac}
