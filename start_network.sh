#!/bin/bash

#开机启动脚本，启动wpa 和 pppd线程

PPPD=$(which pppd)

cat /dev/null > /var/log/zywllog
LOG_FILE=/var/log/zywllog
CUR_TIME=$(date "+%Y-%m-%d %H:%M:%S")
echo "---> $0 start work!@${CUR_TIME}" > ${LOG_FILE}

ps -ef | grep start_network | grep -v grep | awk -F" " '{print $2}' > /var/run/start_network.pid

echo "*/10 * * * * /usr/sbin/ntpdate ntp.api.bz > /dev/null" > /var/spool/cron/crontabs/root
echo "*/10 * * * * /usr/sbin/ntpdate cn.pool.ntp.org > /dev/null" >> /var/spool/cron/crontabs/root

#insmod /root/hardware_ctrl/linux/char/lcd_driver_simulation_spi.ko 
flag=0
feedcount=0

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

while true
do
	sleep 1
	#echo "ssid=${ssid} psk=${psk}"
	ps -ef | grep wpa_supplicant | grep -v grep > /dev/null
	if [ $? -ne 0 ] 
	then 
		#equl 1 mean wpa thread not exists
		ssid=$(cat /root/net.conf | grep -w ssid | awk -F"=" '{print $2}')
		psk=$(cat /root/net.conf | grep -w psk | awk -F"=" '{print $2}')
		CUR_TIME=$(date "+%Y-%m-%d %H:%M:%S")
		echo "---> $0 wlan0 will start@${CUR_TIME}" >> ${LOG_FILE}
		wpa_passphrase ${ssid} ${psk} > /etc/wpa.conf
		echo "ctrl_interface=/var/run/wpa_supplicant" >> /etc/wpa.conf
		wpa_supplicant -iwlan0 -c /etc/wpa.conf > /var/log/wpalog 2>&1 &
		wpa_cli -iwlan0 add_n > /dev/null
	else
		if [ ${flag} -eq 0 ]
		then
			flag=1
			ssid=$(cat /root/net.conf | grep -w ssid | awk -F"=" '{print $2}')
			psk=$(cat /root/net.conf | grep -w psk | awk -F"=" '{print $2}')
			wpa_cli -iwlan0 add_n
			/root/connect_wifi.sh ${ssid} ${psk}
		fi
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
			/root/gpio_ctrl.sh 3 0
			sleep 0.2
			/root/gpio_ctrl.sh 3 1
			sleep 2
			/root/gpio_ctrl.sh 3 0
			/usr/bin/tput reset > /dev/ttyS2
		fi
	fi

	feedcount=$(expr ${feedcount} + 1)
	if [ ${feedcount} -ge 5 ] 
	then
		feedcount=0
		python3 /root/watchdog/watchdog_feed.py > /dev/null 2&>1
	fi  

	if [ -f ${NETFILE} ]
	then
		sta=$(cat ${NETFILE}) 
		if [ "${sta}" == "OK" ]
		then
			num=$(ps -ef | grep mqtt_client | grep -v grep | wc -l)
			if [ ${num} -eq 0 ] 
			then
				start
			elif [ ${num} -gt 1 ] 
			then
				stop
			fi  
		fi  
	fi  
done

