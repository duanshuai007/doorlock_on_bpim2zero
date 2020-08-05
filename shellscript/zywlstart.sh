#!/bin/bash

#开机启动脚本，启动wpa 和 pppd线程

PPPD=$(which pppd)

LOG_FILE=/var/log/zywllog
UPDATESTATUS="/home/ubuntu/update_status"
NETFILE="/root/netstatus"
MACFILE="/tmp/eth0macaddr"
WATCHDOGSCRIPT="/home/watchdog/feed.py"

CUR_TIME=$(date "+%Y-%m-%d %H:%M:%S")
echo "${CUR_TIME}:$0 start work!}" >> ${LOG_FILE}

/bin/dmesg -n 1

#ps -ef | grep start_network | grep -v grep | awk -F" " '{print $2}' > /var/run/start_network.pid

#echo "*/10 * * * * /usr/sbin/ntpdate ntp.api.bz > /dev/null" > /var/spool/cron/crontabs/root
#echo "*/10 * * * * /usr/sbin/ntpdate cn.pool.ntp.org > /dev/null" >> /var/spool/cron/crontabs/root
#echo "*/10 * * * * /bin/bash /root/update_time.sh" >> /var/spool/cron/crontabs/root
#service cron start

cp /root/ntp.conf /etc/

service frpc stop
#timedatectl set-ntp no
#timedatectl
systemctl stop systemd-timesyncd
systemctl disable systemd-timesyncd

#insmod /root/hardware_ctrl/linux/char/lcd_driver_simulation_spi.ko 

cat /dev/null > /tmp/network_timestamp
cat /dev/null > ${NETFILE}
cat /dev/null > ${LOG_FILE}

wpa_connect_flag=0
feedcount=0

mqtt_start() {
	#pid=$(ps -ef | grep mqtt | grep -v grep | awk -F" " '{print $2}')
	mac=$(cat ${MACFILE})
	if [ -n "${mac}" ]
	then
		python3 /root/mqtt_client.py ${mac} &
	else
		mac=$(ifconfig eth0 | grep HWaddr | awk -F" " '{print $5}' | awk -F":" '{print $1$2$3$4$5$6}')
		echo ${mac} > ${MACFILE}
		python3 /root/mqtt_client.py ${mac} &
	fi
}

mqtt_stop() {
	pid=$(ps -ef | grep "mqtt" | grep -v grep | awk -F" " '{print $2}')
	if [ -n "${pid}" ]
	then
		kill ${pid}
		sleep 0.5
		kill -9 ${pid}
	fi
}

mqtt_restart() {
	mqtt_stop
	mqtt_start
}

pppd_stop() {
	pid=$(ps -ef | grep pppd | grep -v grep | awk -F" " '{print $2}')
	if [ -n "${pid}" ]
	then
		kill -INT ${pid}
	fi
}

timecount_for_systemctl=0
timecount_for_pppd=0
wpa_start_error=0
check_pppd_count=0
check_wpa_count=0

#set /tmp/eth0macaddr and set hostname
/root/get_eth0_mac.sh

while true
do
	sleep 1

	#echo "ssid=${ssid} psk=${psk}"
	check_wpa_count=$(expr ${check_wpa_count} + 1)
	if [ ${check_wpa_count} -ge 10 ]
	then
		check_wpa_count=0
		ps -ef | grep wpa_supplicant | grep -v grep > /dev/null
		if [ $? -ne 0 ] 
		then 
			#equl 1 mean wpa thread not exists
			ssid=$(cat /root/net.conf | grep -w ssid | awk -F"=" '{print $2}')
			psk=$(cat /root/net.conf | grep -w psk | awk -F"=" '{print $2}')
			CUR_TIME=$(date "+%Y-%m-%d %H:%M:%S")
			echo "${CUR_TIME}:$0 wlan0 will start" >> ${LOG_FILE}
			wpa_passphrase ${ssid} ${psk} > /etc/wpa.conf
			echo "ctrl_interface=/var/run/wpa_supplicant" >> /etc/wpa.conf
			sleep 0.2
			wpa_supplicant -iwlan0 -c /etc/wpa.conf > /var/log/wpalog 2>&1 &
			sleep 0.2
			wpa_cli -iwlan0 add_n > /dev/null
			wpa_start_error=$(expr ${wpa_start_error} + 1)
		else
			wpa_start_error=0
			if [ ${wpa_connect_flag} -eq 0 ]
			then
				wpa_connect_flag=1
				ssid=$(cat /root/net.conf | grep -w ssid | awk -F"=" '{print $2}')
				psk=$(cat /root/net.conf | grep -w psk | awk -F"=" '{print $2}')
				wpa_cli -iwlan0 add_n
				/root/connect_wifi.sh ${ssid} ${psk}
			fi
		fi
		if [ ${wpa_start_error} -ge 3 ]
		then
			reboot	
			sleep 5
		fi
	fi

	check_pppd_count=$(expr ${check_pppd_count} + 1)
	if [ ${check_pppd_count} -ge 10 ]
	then
		check_pppd_count=0
		ps -ef | grep pppd | grep -v grep > /dev/null
		if [ $? -ne 0 ]
		then
			timecount_for_pppd=0
			python3 ${WATCHDOGSCRIPT}
			python3 /root/check_tty.py
			sleep 0.2
			sta=$(cat /tmp/serial)
			if [ "${sta}" == "OK" ]
			then
				cat /dev/null > /var/log/ppplogfile
				${PPPD} call myapp &
			fi
		else
			timecount_for_pppd=$(expr ${timecount_for_pppd} + 1)
			if [ ${timecount_for_pppd} -ge 5 ]
			then
				timecount_for_pppd=0
				cat /var/log/ppplogfile | grep "Connect script failed" > /dev/null
				if [ $? -eq 0 ]
				then
					pppd_stop
				fi
				#检查ppp0是否获得IP地址
				ifconfig -a | grep ppp0 > /dev/null
				if [ $? -eq 0 ]
				then
					ifconfig ppp0 | grep "inet addr" > /dev/null
					if [ $? -ne 0 ]
					then
						pppd_stop			
					fi
				fi
			fi
		fi
	fi

	feedcount=$(expr ${feedcount} + 1)
	if [ ${feedcount} -ge 5 ] 
	then
		feedcount=0
		python3 ${WATCHDOGSCRIPT}
	fi  

	if [ -f "${UPDATESTATUS}" ]
	then
		sta=$(cat ${UPDATESTATUS} | awk -F":" '{print $1}')
		if [ -n "${sta}" ]
		then
			if [ "${sta}" == "done" ]
			then
				ver=$(cat ${UPDATESTATUS} | awk -F":" '{print $2}')
				no=$(cat ${UPDATESTATUS} | awk -F":" '{print $3}')
				echo "success:${ver}:${no}" > ${UPDATESTATUS}
			elif [ "${sta}" == "success" -o "${sta}" == "error" ]
			then
				#echo "update firmware done!" > /dev/null
				sta=$(cat ${NETFILE}) 
				if [ -z "${sta}" ]
				then
					echo "OK" > ${NETFILE}
				fi
			else
				cat /dev/null > ${NETFILE}
				mqtt_stop
				ps -ef | grep update_firmware | grep -v grep > /dev/null
				if [ $? -ne 0 ]
				then
					feedcount=0
					python3 ${WATCHDOGSCRIPT}
					/root/update_firmware.sh &
				fi
			fi
		fi
#	else
#		timecount_for_systemctl=$(expr ${timecount_for_systemctl} + 1)
#		if [ ${timecount_for_systemctl} -ge 60 ]
#		then
#			timecount_for_systemctl=0
#			feedcount=0
#			python3 ${WATCHDOGSCRIPT}
#			for var in $(systemctl list-unit-files | grep \.service | awk '{print $1}')
#			do  
#				ret=$(systemctl status $var 2>&1 | grep "changed on disk")
#				if [ -n "${ret}" ]
#				then
#					cmd=$(echo ${ret} | awk -F"Run" '{print $2}' | awk -F"'" '{print $2}' | awk -F"'" '{print $1}')
#					#echo "cmd : ${cmd}"
#					${cmd}
#					python3 ${WATCHDOGSCRIPT}
#				fi  
#			done
#			python3 ${WATCHDOGSCRIPT}
#		fi
	fi

	if [ -f ${NETFILE} ]
	then
		sta=$(cat ${NETFILE}) 
		if [ "${sta}" == "OK" ]
		then
			num=$(ps -ef | grep "mqtt" | grep -v grep | wc -l)
			if [ ${num} -eq 0 ] 
			then
				CUR_TIME=$(date "+%Y-%m-%d %H:%M:%S")
				echo "${CUR_TIME}:mqtt client start" >> ${LOG_FILE}
				mqtt_start
			elif [ ${num} -gt 1 ] 
			then
				CUR_TIME=$(date "+%Y-%m-%d %H:%M:%S")
				echo "${CUR_TIME}:mqtt client stop" >> ${LOG_FILE}
				mqtt_stop
			fi  
		fi  
	fi  
done
