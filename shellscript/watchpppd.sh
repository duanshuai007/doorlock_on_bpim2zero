#!/bin/bash

SIGFIL="/root/signal.conf"
EXIT_SIGNAL=$(cat ${SIGFIL} | grep -w SCRIPTEXIT | awk -F"=" '{print $2}')

pppd_start() {
	GET_TIMESTAMP=$(date "+%Y-%m-%d %H:%M:%S")
	echo "${GET_TIMESTAMP}:zywl pppd service start!" >> /var/log/zywllog
	python3 /root/check_tty.py
}

pppd_stop() {
	GET_TIMESTAMP=$(date "+%Y-%m-%d %H:%M:%S")
	echo "${GET_TIMESTAMP}:zywl pppd service stop!" >> /var/log/zywllog
	pid=$(ps -ef | grep check_tty | grep -v grep | awk -F" " '{print $2}')
	kill -${EXIT_SIGNAL} ${pid}
}

case $1 in 
	"start")
		pppd_start
	;;
	"stop")
		pppd_stop
	;;
	*)
	;;
esac