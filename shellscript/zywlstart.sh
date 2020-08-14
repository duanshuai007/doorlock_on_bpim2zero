#!/bin/bash

#开机启动脚本，启动wpa 和 pppd线程

PPPD=$(which pppd)

LOG_FILE="/var/log/zywllog"
UPDATESTATUS="/home/ubuntu/update_status"
UPDATE_END="/home/ubuntu/update_end"
MACFILE="/tmp/eth0macaddr"
SIGFIL="/root/signal.conf"
CONFIG="/root/config.ini"

EXIT_SIGNAL=$(cat ${SIGFIL} | grep -w SCRIPTEXIT | awk -F"=" '{print $2}')
NET_GOOD_SIGNAL=$(cat ${SIGFIL} | grep -w NETWORKOK | awk -F"=" '{print $2}')

GSMSERIAL_SIGNAL=$(cat ${CONFIG} | grep -w gsmserialok | awk -F"=" '{print $2}')
GSMSIMNOTINSERTED_SIGNAL=$(cat ${CONFIG} | grep -w gsmsimnotinserted | awk -F"=" '{print $2}')
GSMSIMMODULEERROR_SIGNAL=$(cat ${CONFIG} | grep -w gsmsimmoduleerror | awk -F"=" '{print $2}')
MQTT_CONN_OK_SIGNAL=$(cat ${CONFIG} | grep -w mqttconnok | awk -F"=" '{print $2}')
MQTT_CONN_BAD_SIGNAL=$(cat ${CONFIG} | grep -w mqttconnbad | awk -F"=" '{print $2}')
DEVICE_UPFATE_SIGNAL=$(cat ${CONFIG} | grep -w deviceupdate | awk -F"=" '{print $2}')

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


eth0macaddr=$(ifconfig eth0 | grep HWaddr | awk -F" " '{print $5}' | awk -F":" '{print $1$2$3$4$5$6}')
echo ${eth0macaddr} > ${MACFILE}
/bin/hostname zywldl${eth0macaddr}

pppd_stop() {
	pid=$(ps -ef | grep pppd | grep -v grep | awk -F" " '{print $2}')
	if [ -n "${pid}" ]
	then
		kill -INT ${pid}
	fi
}

wpa_connect_flag=0
wpa_start_error=0
check_pppd_count=0
check_wpa_count=0
check_temp_time=0
pppd_wait_count=0
gsmserial_status=0
network_status=0
sim_module_error=0
check_pppd_cycle=0
mqtt_conn_status=0
monitor_close=0
mqtt_run_status=0
firmware_update_flag=0
pppd_not_have_online_func_count=0
exit_flag=0

thread_exit() {
	exit_flag=1
}

network_status_is_ok(){
	echo "network is ok" >> ${LOG_FILE}
	network_status=1
}

#sim module运行正常,可以启动pppd程序
gsmserial_status_is_ok() {
	echo "gsm serial is ok" >> ${LOG_FILE}
	gsmserial_status=1
	sim_module_error=0
	systemctl stop zywlpppd
}
#sim module检测到没有sim card
gsm_sim_not_inserted() {
	systemctl stop zywlpppd
	echo "sim card not inserted" >> ${LOG_FILE}
	sim_module_error=1
	gsmserial_status=0
	pppd_stop
}
#sim module检测到有sim卡，但是sim卡不能注册到网络
gsm_sim_module_error() {
	systemctl stop zywlpppd
	echo "sim card can't register!" >> ${LOG_FILE}
	sim_module_error=1
	gsmserial_status=0
	pppd_stop
}

mqtt_connect_status_is_bad(){
	mqtt_conn_status=0
	echo "mqtt connect bad" >> ${LOG_FILE}
}
mqtt_connect_status_is_ok(){
	mqtt_conn_status=1
	echo "mqtt connect ok" >> ${LOG_FILE}
}
device_will_update(){
	firmware_update_flag=1
	echo "i will update firmware" >> ${LOG_FILE}
}

trap "thread_exit" ${EXIT_SIGNAL}
trap "gsmserial_status_is_ok" ${GSMSERIAL_SIGNAL}
trap "network_status_is_ok" ${NET_GOOD_SIGNAL}
trap "gsm_sim_not_inserted" ${GSMSIMNOTINSERTED_SIGNAL}
trap "gsm_sim_module_error" ${GSMSIMMODULEERROR_SIGNAL}
trap "mqtt_connect_status_is_bad" ${MQTT_CONN_BAD_SIGNAL}
trap "mqtt_connect_status_is_ok" ${MQTT_CONN_OK_SIGNAL}
trap "device_will_update" ${DEVICE_UPFATE_SIGNAL}

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
		/root/zywlmonitor.sh $$ &
	fi
}

if [ -f "${UPDATE_END}" ];then
	network_status=1
fi

if [ -f "${UPDATESTATUS}" ];then
	firmware_update_flag=1
fi

while true
do
	sleep 1

	if [ ${exit_flag} -eq 1 ];then
		exit
	fi

	if [ ${mqtt_conn_status} -eq 1 ];then
		if [ ${monitor_close} -eq 1 ];then
			monitor_close=0
			monitor_thread_exit
		fi
	else
		if [ ${monitor_close} -eq 0 ];then
			monitor_close=1
			monitor_thread_start
			network_status=0
		fi
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
					${PPPD} call myapp &
				else
					systemctl start zywlpppd
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
						pppd_not_have_online_func_count=$(expr ${pppd_not_have_online_func_count} + 1)
					else
						pppd_not_have_online_func_count=0
					fi
				else
					gsmserial_status=0
					pppd_wait_count=$(expr ${pppd_wait_count} + 1)
				fi
				if [ ${pppd_wait_count} -ge 2 ];then
					pppd_wait_count=0
					pppd_stop
					systemctl start zywlpppd
				fi
				if [ ${pppd_not_have_online_func_count} -ge 3 ];then
					systemctl stop zywlpppd
					pppd_stop
					sim_module_error=1
				fi
			fi
		fi
	fi

	if [ ${firmware_update_flag} -eq 1 ];then
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
					systemctl stop zywlmqtt
					ps -ef | grep update_firmware | grep -v grep > /dev/null
					if [ $? -ne 0 ]
					then
						#feedcount=0
						#python3 ${WATCHDOGSCRIPT}
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
		else
			firmware_update_flag=0
		fi
	fi

	if [ ${network_status} -eq 1 ];then
		if [ ${mqtt_run_status} -eq 0 ];then
			mqtt_run_status=1
			/root/update_time.sh
			systemctl start zywlmqtt
		fi
	else
		if [ ${mqtt_run_status} -eq 1 ];then
			mqtt_run_status=0
			systemctl stop zywlmqtt
		fi
	fi  
done
