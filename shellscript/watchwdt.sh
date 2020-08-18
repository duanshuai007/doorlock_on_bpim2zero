#!/bin/bash

SIGFIL="/root/signal.conf"
STOPWDT_SIGNAL=$(cat ${SIGFIL} | grep -w SCRIPTEXIT | awk -F"=" '{print $2}')
FEEDWDT_SIGNAL=$(cat ${SIGFIL} | grep -w FEEDWDT | awk -F"=" '{print $2}')

wdt_start(){
	cat /dev/null > /tmp/zywlwdt.pid
	python3 /root/feed.py ${FEEDWDT_SIGNAL} ${STOPWDT_SIGNAL}
}

wdt_stop(){
	pid=$(ps -ef | grep feed | grep -v grep | awk -F" " '{print $2}')
	if [ -n "${pid}" ];then
		kill -${STOPWDT_SIGNAL} ${pid}
	fi
	rm /tmp/zywlwdt.pid
}

case $1 in
	"start")
		wdt_start
		;;
	"stop")
		wdt_stop
		;;
	*)
esac
