#!/bin/bash

NETTIMESTAMP=/tmp/network_timestamp
service ntp stop
CUR_TIME=$(date "+%Y-%m-%d %H:%M:%S")
#echo "${CUR_TIME}:ntpupdate ntp.api.bz" >> /var/log/ntpdate.log
/usr/sbin/ntpdate ntp.api.bz
if [ $? -ne 0 ]
then
	#echo "${CUR_TIME}:ntpupdate cn.pool.ntp.org" >> /var/log/ntpdate.log
	/usr/sbin/ntpdate cn.pool.ntp.org
fi
service ntp start
echo 0 > ${NETTIMESTAMP}
