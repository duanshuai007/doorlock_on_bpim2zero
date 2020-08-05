#!/bin/bash

all_start() {
	#echo "start all"
	GET_TIMESTAMP=$(date "+%Y-%m-%d %H:%M:%S")
	echo "${GET_TIMESTAMP}:zywldl service start!" >> /var/log/monitor.log
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
	#echo "stop all"
	GET_TIMESTAMP=$(date "+%Y-%m-%d %H:%M:%S")
	echo "${GET_TIMESTAMP}:zywldl service stop!" >> /var/log/monitor.log
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

	pid=$(ps -ef | grep "zywl_moni_wlan" | grep -v watch | grep -v grep | awk -F" " '{print $2}')
	if [ -n "${pid}" ]
	then
		kill -9 ${pid}
	fi
		
	pid=$(ps -ef | grep "zywl_moni_eth" | grep -v watch | grep -v grep | awk -F" " '{print $2}')
	if [ -n "${pid}" ]
	then
		kill -9 ${pid}
	fi

	pid=$(ps -ef | grep "zywl_moni_ppp" | grep -v watch | grep -v grep | awk -F" " '{print $2}')
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

mqtt_stop() {
	cat /dev/null > /tmp/netstatus
	pid=$(ps -ef | grep "mqtt" |  grep -v watch | grep -v grep | awk -F" " '{print $2}')
	if [ -n "${pid}" ]
	then
		kill ${pid}
	fi
}

mqtt_start() {
	echo "OK" > /tmp/netstatus
}

mqtt_restart() {
	mqtt_stop
	sleep 1
	mqtt_start
}

start_network_stop() {
	pid=$(ps -ef | grep "zywlstart" | grep -v grep | awk -F" " '{print $2}')
	if [ -n "${pid}" ]
	then
		kill ${pid}
	fi
}

monitor_network_stop() {
	pid=$(ps -ef | grep "zywlmonitor" | grep -v grep | awk -F" " '{print $2}')
	if [ -n "${pid}" ]
	then
		kill ${pid}
	fi

	pid=$(ps -ef | grep "zywl_moni_wlan" | grep -v watch | grep -v grep | awk -F" " '{print $2}')
	if [ -n "${pid}" ]
	then
		kill -9 ${pid}
	fi
		
	pid=$(ps -ef | grep "zywl_moni_eth" | grep -v watch | grep -v grep | awk -F" " '{print $2}')
	if [ -n "${pid}" ]
	then
		kill -9 ${pid}
	fi

	pid=$(ps -ef | grep "zywl_moni_ppp" | grep -v watch | grep -v grep | awk -F" " '{print $2}')
	if [ -n "${pid}" ]
	then
		kill -9 ${pid}
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
				mqtt_stop
			;;
			"start")
				mqtt_start
			;;
			"restart")
				mqtt_restart
			;;
		esac
	;;
	"zywlstart.sh")
		case $2 in
			"stop")
				start_network_stop
			;;
			"restart")
				start_network_stop
				/root/zywlstart.sh &
			;;
		esac
	;;
	"zywlmonitor.sh")
		case $2 in
			"stop")
				monitor_network_stop
			;;
			"restart")
				monitor_network_stop
				/root/zywlmonitor.sh &
			;;
		esac
	;;
	*)
	;;
esac
