#!/bin/bash
#该脚本用于调试使用
#注意！！！
#如果开启了开门狗，使用该脚本关闭所有程序后会在开门狗超时候导致设备重启。
start() {
	#pid=$(ps -ef | grep mqtt | grep -v grep | awk -F" " '{print $2}')
	mac=$(cat /tmp/eth0macaddr)
	python3 /root/mqtt_client.py ${mac} &
}

stop() {
	pid=$(ps -ef | grep mqtt_client | grep -v grep | awk -F" " '{print $2}')
	if [ ! -z "${pid}" ]
	then
		kill -9 ${pid}
	fi
}

restart() {
	stop
	start
}

NETFILE="/tmp/netstatus"

feedcount=0
while true
do
	sleep 1
	if [ -f ${NETFILE} ]
	then
		sta=$(cat ${NETFILE}) 
		if [ "${sta}" == "OK" ]
		then
			#pid=$(ps -ef | grep mqtt_client | grep -v grep | awk -F" " '{print $2}')
			#if [ -z "${pid}" ]
			num=$(ps -ef | grep mqtt_client | grep -v grep | wc -l)
			#	echo "num=${num}"
			if [ ${num} -eq 0 ]
			then
				start
			elif [ ${num} -gt 1 ]
			then
				stop
			fi
		fi
	fi

	feedcount=$(expr ${feedcount} + 1)
	if [ ${feedcount} -ge 5 ]
	then
		feedcount=0
		python3 /root/watchdog/watchdog_feed.py > /dev/null 2&>1
		#GET_TIMESTAMP=$(date "+%Y-%m-%d %H:%M:%S")
		#echo "${GET_TIMESTAMP} feed watchdog"
	fi
done
