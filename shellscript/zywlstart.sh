#!/bin/bash

#开机启动脚本，启动wpa 和 pppd线程

PPPD=$(which pppd)

LOG_FILE="/var/log/zywllog"
UPDATESTATUS="/home/ubuntu/update_status"
UPDATE_END="/home/ubuntu/update_end"
MACFILE="/tmp/eth0macaddr"
WATCHDOGSCRIPT="/home/watchdog/feed.py"
SIGFIL="/root/signal.conf"

EXIT_SIGNAL=$(cat ${SIGFIL} | grep -w SCRIPTEXIT | awk -F"=" '{print $2}')
GSMSERIAL_SIGNAL=$(cat /root/config.ini | grep -w GSMSERIALOK | awk -F"=" '{print $2}')
GSMSIMNOTINSERTED_SIGNAL=$(cat /root/config.ini | grep -w GSMSIMNOTINSERTED | awk -F"=" '{print $2}')
GSMSIMMODULEERROR_SIGNAL=$(cat /root/config.ini | grep -w GSMSIMMODULEERROR | awk -F"=" '{print $2}')
NET_GOOD_SIG=$(cat ${SIGFIL} | grep -w NETWORKOK | awk -F"=" '{print $2}')
NET_BAD_SIG=$(cat ${SIGFIL} | grep -w NETWORKBAD | awk -F"=" '{print $2}')
MQTT_CONN_OK_SIG=$(cat /root/config.ini | grep -w MQTTCONNOK | awk -F"=" '{print $2}')
MQTT_CONN_BAD_SIG=$(cat /root/config.ini | grep -w MQTTCONNBAD | awk -F"=" '{print $2}')

CUR_TIME=$(date "+%Y-%m-%d %H:%M:%S")
echo "${CUR_TIME}:$0 start work!" >> ${LOG_FILE}

/bin/dmesg -n 1

#echo "*/10 * * * * /usr/sbin/ntpdate ntp.api.bz > /dev/null" > /var/spool/cron/crontabs/root
#service cron start

cp /root/ntp.conf /etc/

service frpc stop
#timedatectl set-ntp no
#timedatectl
systemctl stop systemd-timesyncd
systemctl disable systemd-timesyncd

cat /dev/null > /tmp/network_timestamp
cat /dev/null > ${LOG_FILE}

wpa_connect_flag=0
feedcount=0

eth0macaddr=$(ifconfig eth0 | grep HWaddr | awk -F" " '{print $5}' | awk -F":" '{print $1$2$3$4$5$6}')
echo ${eth0macaddr} > ${MACFILE}
/bin/hostname zywldl${eth0macaddr}

mqtt_start() {
	python3 /root/mqtt_client.py ${eth0macaddr} &
}

mqtt_stop() {
	pid=$(ps -ef | grep "mqtt" | grep -v grep | awk -F" " '{print $2}')
	if [ -n "${pid}" ]
	then
		kill -${EXIT_SIGNAL} ${pid}
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

wpa_start_error=0
check_pppd_count=0
check_wpa_count=0
check_temp_time=0
pppd_wait_count=0
gsmserial_status=0
network_status=0
sim_not_insert=0
sim_module_error=0
check_pppd_cycle=0
mqtt_conn_status=0
exit_flag=0

thread_exit() {
	exit_flag=1
}

gsmserial_status_is_ok() {
	echo "gsm serial is ok" >> ${LOG_FILE}
	gsmserial_status=1
	sim_not_insert=0
	sim_module_error=0
	systemctl stop zywlpppd
}

network_status_is_ok(){
	echo "network is ok" >> ${LOG_FILE}
	network_status=1
}

network_status_is_bad(){
	echo "network is bad" >> ${LOG_FILE}
	network_status=0
}

gsm_sim_not_inserted() {
	systemctl stop zywlpppd
	echo "sim card not inserted" >> ${LOG_FILE}
	sim_not_insert=1
	pppd_stop
}

gsm_sim_module_error() {
	systemctl stop zywlpppd
	echo "sim module error!" >> ${LOG_FILE}
	pppd_stop
	sim_module_error=1
}

mqtt_connect_status_is_bad(){
	mqtt_conn_status=0
	echo "mqtt connect bad" >> ${LOG_FILE}
}
mqtt_connect_status_is_ok(){
	mqtt_conn_status=1
	echo "mqtt connect ok" >> ${LOG_FILE}
}

trap "thread_exit" ${EXIT_SIGNAL}
trap "gsmserial_status_is_ok" ${GSMSERIAL_SIGNAL}
trap "network_status_is_ok" ${NET_GOOD_SIG}
trap "network_status_is_bad" ${NET_BAD_SIG}
trap "gsm_sim_not_inserted" ${GSMSIMNOTINSERTED_SIGNAL}
trap "gsm_sim_module_error" ${GSMSIMMODULEERROR_SIGNAL}
trap "mqtt_connect_status_is_bad" ${MQTT_CONN_BAD_SIG}
trap "mqtt_connect_status_is_ok" ${MQTT_CONN_OK_SIG}

#set /tmp/eth0macaddr and set hostname

python3 /root/showimage.py 1

time_sync() {
	ps -ef | grep ntpd | grep -v grep > /dev/null
	if [ $? -ne 0 ];then
		pid=$(ps -ef | grep update_time | grep -v grep | awk -F" " '{print $2}')
		if [ -z "${pid}" ];then
			service ntp start
		fi  
	fi  
}

monitor_thread_exit(){
	pid=$(ps -ef | grep zywlmonitor | grep -v grep | awk -F" " '{print $2}')
	if [ -n "${pid}" ];then
		kill -${EXIT_SIGNAL} ${pid}
	fi
}

monitor_thread_start(){
	ps -ef | grep zywlmonitor | grep -v grep > /dev/null
	if [ $? -ne 0 ];then
		/root/zywlmonitor.sh &
	fi
}

while true
do
	sleep 1

	if [ ${exit_flag} -eq 1 ];then
		exit
	fi

	if [ ${mqtt_conn_status} -eq 1 ];then
		monitor_thread_exit
	else
		monitor_thread_start
	fi

	check_temp_time=$(expr ${check_temp_time} + 1)
	if [ ${check_temp_time} -ge 600 ];then
		check_temp_time=0
		temp=$(cat /sys/class/thermal/thermal_zone0/temp)
		CUR_TIME=$(date "+%Y-%m-%d %H:%M:%S")
		echo "${CUR_TIME}:current temp = ${temp}" >> /var/log/monitor.log
	fi

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

	if [ ${sim_module_error} -eq 0 ];then
		check_pppd_count=$(expr ${check_pppd_count} + 1)
		if [ ${check_pppd_count} -ge 10 ];then
			check_pppd_count=0
			ps -ef | grep -w pppd | grep -v grep > /dev/null
			if [ $? -ne 0 ];then
				if [ ${gsmserial_status} -eq 1 ];then
					cat /dev/null > /var/log/ppplogfile
#systemctl stop zywlpppd
#					sleep 2
					${PPPD} call myapp &
				else
					if [ ${sim_not_insert} -eq 0 ];then
						systemctl start zywlpppd
					fi
				fi
			else
				cat /var/log/ppplogfile | grep "Connect script failed" > /dev/null
				if [ $? -eq 0 ];then
					gsmserial_status=0
					pppd_wait_count=$(expr ${pppd_wait_count} + 1)
				fi
				#检查ppp0是否获得IP地址
				ip addr | grep ppp0 > /dev/null
				if [ $? -eq 0 ];then
					ip addr | grep ppp0 | grep inet > /dev/null
					if [ $? -ne 0 ];then
						gsmserial_status=0
						pppd_wait_count=$(expr ${pppd_wait_count} + 1)
					fi
				else
					gsmserial_status=0
					pppd_wait_count=$(expr ${pppd_wait_count} + 1)
				fi
				if [ ${pppd_wait_count} -ge 3 ];then
					pppd_wait_count=0
					pppd_stop
					if [ ${sim_not_insert} -eq 0 ];then
						systemctl start zywlpppd
					fi
				fi	
			fi
		fi
	fi

	feedcount=$(expr ${feedcount} + 1)
	if [ ${feedcount} -ge 5 ];then
		feedcount=0
		python3 ${WATCHDOGSCRIPT}
	fi  

	if [ -f "${UPDATESTATUS}" ];then
		sta=$(cat ${UPDATESTATUS} | awk -F":" '{print $1}')
		if [ -n "${sta}" ];then
			if [ "${sta}" == "done" ];then
				ver=$(cat ${UPDATESTATUS} | awk -F":" '{print $2}')
				no=$(cat ${UPDATESTATUS} | awk -F":" '{print $3}')
				echo "success:${ver}:${no}" > ${UPDATESTATUS}
				sync
			elif [ "${sta}" == "success" -o "${sta}" == "error" ];then
				#echo "update firmware done!" > /dev/null
				if [ ! -f "${UPDATE_END}" ];then
					touch ${UPDATE_END}
					sync
					systemctl restart zywldl
				fi
			elif [ "${sta}" == "start" -o "${sta}" == "move" -o "${sta}" == "clear" ];then
				network_status=0
				mqtt_stop
				ps -ef | grep update_firmware | grep -v grep > /dev/null
				if [ $? -ne 0 ]
				then
					feedcount=0
					python3 ${WATCHDOGSCRIPT}
					/root/update_firmware.sh &
				fi
			else
				rm ${UPDATESTATUS}
				echo "update firmware: rm update_status file sta:${sta}" >> ${LOG_FILE}
				network_status=1
			fi
		else
			#如果UPDATESTATUS文件因为某些原因导致没有内容写入，那么就删除该文件
			rm ${UPDATESTATUS}
			echo "update firmware: rm update_status file sta is null" >> ${LOG_FILE}
			network_status=1
		fi
#			for var in $(systemctl list-unit-files | grep \.service | awk '{print $1}')
#				ret=$(systemctl status $var 2>&1 | grep "changed on disk")
	fi

	if [ -f ${UPDATE_END} ];then
		network_status=1
	fi

	time_sync

	if [ ${network_status} -eq 1 ];then
		num=$(ps -ef | grep "mqtt" | grep -v grep | wc -l)
		if [ ${num} -eq 0 ];then
			CUR_TIME=$(date "+%Y-%m-%d %H:%M:%S")
			echo "${CUR_TIME}:mqtt client start" >> ${LOG_FILE}
			/root/update_time.sh
			#systemctl restart frpc
			mqtt_start
		elif [ ${num} -ge 2 ];then
			CUR_TIME=$(date "+%Y-%m-%d %H:%M:%S")
			echo "${CUR_TIME}:mqtt client stop" >> ${LOG_FILE}
			mqtt_stop
		fi  
	fi  
done
