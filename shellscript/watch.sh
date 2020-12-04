#!/bin/bash
SIGFIL="/root/signal.conf"
LOGFIL="/var/log/zywllog"

EXIT_SIGNAL=$(cat ${SIGFIL} | grep -w SCRIPTEXIT | awk -F"=" '{print $2}')

all_start() {
	GET_TIMESTAMP=$(date "+%Y-%m-%d %H:%M:%S")
	echo "${GET_TIMESTAMP}:zywldl service start!" >> ${LOGFIL}
	ps -ef | grep "zywlstart" | grep -v grep > /dev/null
	if [ $? -ne 0 ]
	then
		/root/zywlstart.sh
	fi
}

all_stop() {
	GET_TIMESTAMP=$(date "+%Y-%m-%d %H:%M:%S")
	echo "${GET_TIMESTAMP}:zywldl service stop!" >> ${LOGFIL}
	pid=$(ps -ef | grep "zywlstart" | grep -v grep | awk -F" " '{print $2}')
	if [ -n "${pid}" ]
	then
		kill -${EXIT_SIGNAL} ${pid}
	fi
	
	pid=$(ps -ef | grep "zywlmonitor" | grep -v grep | awk -F" " '{print $2}')
	if [ -n "${pid}" ]
	then
		kill -${EXIT_SIGNAL} ${pid}
	fi

	pid=$(ps -ef | grep "zywl_moni_wlan" | grep -v watch | grep -v grep | awk -F" " '{print $2}')
	if [ -n "${pid}" ]
	then
		kill -${EXIT_SIGNAL} ${pid}
	fi
		
	pid=$(ps -ef | grep "zywl_moni_eth" | grep -v watch | grep -v grep | awk -F" " '{print $2}')
	if [ -n "${pid}" ]
	then
		kill -${EXIT_SIGNAL} ${pid}
	fi

	pid=$(ps -ef | grep "zywl_moni_ppp" | grep -v watch | grep -v grep | awk -F" " '{print $2}')
	if [ -n "${pid}" ]
	then
		kill -${EXIT_SIGNAL} ${pid}
	fi

	systemctl stop zywlmqtt
	systemctl stop zywlpppd
	systemctl stop zywlnet
	sleep 2
}

all_restart() {
	all_stop
	sleep 1
	all_start
}

case $1 in
	"start")
		all_start
	;;
	"stop")
		all_stop
	;;
	"restart")
		all_restart
	;;
	*)
	;;
esac
