#!/bin/bash

#
#	监视ppp网络状态
#
STATEFILE="/tmp/ppp0status"
PPPLOGFILE="/var/log/ppplogfile"
TESTDNSSERVER="8.8.8.8"

error_count=0

pppd_stop() {
	pid=$(ps -ef | grep pppd | grep -v grep | awk -F" " '{print $2}')
	if [ -n "${pid}" ]
	then
		kill -INT ${pid}
	fi  
}

while true
do
	sleep 5

	cat ${PPPLOGFILE} | grep "Serial connection established" > /dev/null
	if [ $? -ne 0 ]
	then
		#not find this string，mean pppd run wrong
		cat /dev/null > ${STATEFILE}
	else
		route -n | grep ${TESTDNSSERVER} | grep ppp0 > /dev/null
		if [ $? -ne 0 ]
		then
			route add ${TESTDNSSERVER} ppp0
			sleep 1
		fi

		ping ${TESTDNSSERVER} -I ppp0 -c 1 > /dev/null
		if [ $? -eq 0 ]
		then
			error_count=0
			echo "OK" > ${STATEFILE}
		else
			error_count=$(expr ${error_count} + 1)
			if [ ${error_count} -ge 3 ]
			then
				error_count=0
				pppd_stop
				cat /dev/null > ${STATEFILE}
			fi
		fi
	fi
done
