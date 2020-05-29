#!/bin/bash

#开机启动脚本，启动wpa 和 pppd线程

PPPD=$(which pppd)

cat /dev/null > /var/log/zywllog
LOG_FILE=/var/log/zywllog
CUR_TIME=$(date "+%Y-%m-%d %H:%M:%S")
echo "---> $0 start work!@${CUR_TIME}" > ${LOG_FILE}
SAVE_PID_FLAG=0
DEFAULT_NET=$(cat /root/net.conf | grep choice | awk -F"=" '{print $2}')

ps -ef | grep start_network | grep -v grep | awk -F" " '{print $2}' > /var/run/start_network.pid

while true
do
	sleep 5

	ps -ef | grep wpa_supplicant | grep -v grep > /dev/null
	if [ $? -ne 0 ] 
	then 
		#equl 1 mean wpa thread not exists
		CUR_TIME=$(date "+%Y-%m-%d %H:%M:%S")
		echo "---> $0 wlan0 will start@${CUR_TIME}" >> ${LOG_FILE}
		wpa_supplicant -iwlan0 -c /etc/wpa.conf > /var/log/wpalog 2>&1 &
	fi

	ps -ef | grep pppd | grep -v grep > /dev/null
	if [ $? -ne 0 ]
	then
		python3 /root/check_tty.py
		sleep 0.5

		sta=$(cat /tmp/serial)

		CUR_TIME=$(date "+%Y-%m-%d %H:%M:%S")
		if [ "$sta" == "OK" ]
		then
			echo "---> $0 ppp0 will start@${CUR_TIME}" >> ${LOG_FILE}
			${PPPD} call myapp &
		else
			echo "---> $0 serial not work@${CUR_TIME}" >> ${LOG_FILE}
		fi
	fi

	sleep 25
done

