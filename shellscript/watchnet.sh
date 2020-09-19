#!/bin/bash

SIGFIL="/root/signal.conf"
MACFILE="/tmp/eth0macaddr"

EXIT_SIGNAL=$(cat ${SIGFIL} | grep -w SCRIPTEXIT | awk -F"=" '{print $2}')

netmonitor_start() {
	GET_TIMESTAMP=$(date "+%Y-%m-%d %H:%M:%S")
	echo "${GET_TIMESTAMP}:zywl netmonitor service start!" >> /var/log/zywllog
	pid=$(ps -ef | grep zywlstart | grep -v grep | awk -F" " '{print $2}')
	/root/zywlmonitor.sh ${pid}
}

netmonitor_stop() {
	GET_TIMESTAMP=$(date "+%Y-%m-%d %H:%M:%S")
	echo "${GET_TIMESTAMP}:zywl netmonitor service stop!" >> /var/log/zywllog
	while true
	do
		pid=$(ps -ef | grep zywlmonitor | grep -v grep | awk -F" " '{print $2}')
		if [ -n "${pid}" ];then
			kill -${EXIT_SIGNAL} ${pid}
			sleep 1
		else
			break
		fi
	done
}

case $1 in 
	"start")
		netmonitor_start
	;;
	"stop")
		netmonitor_stop
	;;
	*)
	;;
esac
