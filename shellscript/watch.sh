#!/bin/bash
SIGFIL="/root/signal.conf"
EXIT_SIGNAL=$(cat ${SIGFIL} | grep -w SCRIPTEXIT | awk -F"=" '{print $2}')

all_start() {
	#echo "start all"
	GET_TIMESTAMP=$(date "+%Y-%m-%d %H:%M:%S")
	echo "${GET_TIMESTAMP}:zywldl service start!" >> /var/log/monitor.log
	ps -ef | grep "zywlstart" | grep -v grep > /dev/null
	if [ $? -ne 0 ]
	then
		/root/zywlstart.sh
	fi
}

all_stop() {
	#echo "stop all"
	GET_TIMESTAMP=$(date "+%Y-%m-%d %H:%M:%S")
	echo "${GET_TIMESTAMP}:zywldl service stop!" >> /var/log/monitor.log
	python3 /home/watchdog/feed.py
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

	pid=$(ps -ef | grep "mqtt" |  grep -v watch | grep -v grep | awk -F" " '{print $2}')
	if [ -n "${pid}" ]
	then
		kill -${EXIT_SIGNAL} ${pid}
		sleep 1
		kill -9 ${pid}
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
}

all_restart() {
	all_stop
	sleep 1
	all_start
}


if [ $# -lt 1 ]
then
	echo "should run like this"
	echo "./watch.sh start/stop/restart"
	exit
fi

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
