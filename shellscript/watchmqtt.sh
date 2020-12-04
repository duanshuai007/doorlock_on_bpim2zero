#!/bin/bash

SIGFIL="/root/signal.conf"
MACFILE="/tmp/eth0macaddr"

EXIT_SIGNAL=$(cat ${SIGFIL} | grep -w SCRIPTEXIT | awk -F"=" '{print $2}')

mqtt_start() {
	GET_TIMESTAMP=$(date "+%Y-%m-%d %H:%M:%S")
	echo "${GET_TIMESTAMP}:zywl mqtt service start!" >> /var/log/zywllog
	pid=$(ps -ef | grep zywlstart | grep -v grep | awk -F" " '{print $2}')
	mac=$(cat ${MACFILE})
	python3 /root/mqtt_client.py ${mac} ${pid}
}

mqtt_stop() {
	GET_TIMESTAMP=$(date "+%Y-%m-%d %H:%M:%S")
	echo "${GET_TIMESTAMP}:zywl mqtt service stop!" >> /var/log/zywllog
	while true
	do
		pid=$(ps -ef | grep mqtt_client | grep -v grep | awk -F" " '{print $2}')
		if [ -n "${pid}" ];then
			kill -${EXIT_SIGNAL} ${pid}
			sleep 1
			kill -9 ${pid}
			sleep 1
		else
			break
		fi
	done
}

case $1 in 
	"start")
		mqtt_start
	;;
	"stop")
		mqtt_stop
	;;
	*)
	;;
esac
