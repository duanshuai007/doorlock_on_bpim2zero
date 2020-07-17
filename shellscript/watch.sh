#!/bin/bash

all_start() {
	echo "start all"
	ps -ef | grep "zywlstart" | grep -v grep > /dev/null
	if [ $? -ne 0 ]
	then
		/root/zywlstart.sh &
	fi

	ps -ef | grep "zywlmonitor" | grep -v grep > /dev/null
	if [ $? -ne 0 ]
	then
		/root/zywlmonitor.sh &
	fi
}

all_stop() {
	echo "stop all"
	python3 /home/watchdog/feed.py
	pid=$(ps -ef | grep "zywlstart" | grep -v grep | awk -F" " '{print $2}')
	if [ -n "${pid}" ]
	then
		kill -9 ${pid}
	fi
	
	pid=$(ps -ef | grep "zywlmonitor" | grep -v grep | awk -F" " '{print $2}')
	if [ -n "${pid}" ]
	then
		kill -9 ${pid}
	fi

	pid=$(ps -ef | grep "mqtt" |  grep -v watch | grep -v grep | awk -F" " '{print $2}')
	if [ -n "${pid}" ]
	then
		kill -9 ${pid}
	fi
}

all_restart() {
	all_stop
	sleep 1
	all_start
}

mqtt_kill() {
	pid=$(ps -ef | grep "mqtt" |  grep -v watch | grep -v grep | awk -F" " '{print $2}')
	if [ -n "${pid}" ]
	then
		kill ${pid}
	fi
}

start_network_kill() {
	pid=$(ps -ef | grep "zywlstart" | grep -v grep | awk -F" " '{print $2}')
	if [ -n "${pid}" ]
	then
		kill ${pid}
	fi
}

monitor_network_kill() {
	pid=$(ps -ef | grep "zywlmonitor" | grep -v grep | awk -F" " '{print $2}')
	if [ -n "${pid}" ]
	then
		kill ${pid}
	fi
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
	"mqtt")
		case $2 in
			"stop")
				cat /dev/null > /tmp/netstatus
				mqtt_kill
			;;
			"start")
				echo "OK" > /tmp/netstatus
			;;
			"restart")
			;;
		esac
	;;
	"zywlstart.sh")
		case $2 in
			"stop")
				start_network_kill
			;;
			"restart")
				start_network_kill
				/root/zywlstart.sh &
			;;
		esac
	;;
	"zywlmonitor.sh")
		case $2 in
			"stop")
				monitor_network_kill
			;;
			"restart")
				monitor_network_kill
				/root/zywlmonitor.sh &
			;;
		esac
	;;
	*)
	;;
esac
