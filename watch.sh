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

mqtt_restart() {
	pid=$(ps -ef | grep mqtt_client | grep -v grep | awk -F" " '{print $2}')
	if [ -n "${pid}" ]
	then
		kill ${pid}
	fi
}

start_network_restart() {
	pid=$(ps -ef | grep start_network | grep -v grep | awk -F" " '{print $2}')
	if [ -n "${pid}" ]
	then
		kill ${pid}
	fi
}

monitor_network_restart() {
	pid=$(ps -ef | grep monitor_network | grep -v grep | awk -F" " '{print $2}')
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
		start
	;;
	"stop")
		stop
	;;
	"restart")
		restart
	;;
	"mqtt")
		case $2 in
			"restart")
				mqtt_restart
				;;
		esac
	;;
	"start_network.sh")
		case $2 in
			"restart")
				start_network_restart
				/root/start_network.sh &
			;;
		esac
	;;
	"monitor_network.sh")
		case $2 in
			"restart")
				monitor_network_restart
				/root/monitor_network.sh &
			;;
		esac
	;;
	*)
	;;
esac
