#!/bin/bash

start() {
	echo "start all"
	/root/start_network.sh &
	/root/monitor_network.sh &
}

stop() {
	echo "stop all"
	pid=$(ps -ef | grep start_network | grep -v grep | awk -F" " '{print $2}')
	if [ -n "${pid}" ]
	then
		kill -9 ${pid}
	fi
	
	pid=$(ps -ef | grep monitor_network | grep -v grep | awk -F" " '{print $2}')
	if [ -n "${pid}" ]
	then
		kill -9 ${pid}
	fi

	pid=$(ps -ef | grep mqtt_client | grep -v grep | awk -F" " '{print $2}')
	if [ -n "${pid}" ]
	then
		kill -9 ${pid}
	fi
}

restart() {
	stop
	sleep 1
	start
}

if [ $# -lt 1 ]
then
	echo "should run like this"
	echo "./watch.sh start/stop/restart"
	exit
fi

case $1 in
	"start")
		start
	;;
	"stop")
		stop
	;;
	"restart")
		restart
	;;
	*)
	;;
esac
