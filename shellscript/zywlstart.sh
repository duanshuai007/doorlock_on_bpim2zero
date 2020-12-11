#!/bin/bash

#开机启动脚本，启动wpa 和 pppd线程

PPPD=$(which pppd)

LOGFILE="/var/log/zywllog"
UPDATESTATUS="/home/update_status"
UPDATE_END="/home/update_end"
MACFILE="/tmp/eth0macaddr"
SIGFIL="/root/signal.conf"
CONFIG="/root/config.ini"

EXIT_SIGNAL=$(cat ${SIGFIL} | grep -w SCRIPTEXIT | awk -F"=" '{print $2}')
NET_GOOD_SIGNAL=$(cat ${SIGFIL} | grep -w NETWORKOK | awk -F"=" '{print $2}')
NET_BAD_SIGNAL=$(cat ${SIGFIL} | grep -w NETWORKBAD | awk -F"=" '{print $2}')
FEEDWDT_SIGNAL=$(cat ${SIGFIL} | grep -w FEEDWDT | awk -F"=" '{print $2}')

GSMSERIAL_SIGNAL=$(cat ${CONFIG} | grep -w gsmserialok | awk -F" = " '{print $2}')
GSMSIMNOTINSERTED_SIGNAL=$(cat ${CONFIG} | grep -w gsmsimnotinserted | awk -F" = " '{print $2}')
GSMSIMMODULEERROR_SIGNAL=$(cat ${CONFIG} | grep -w gsmsimmoduleerror | awk -F" = " '{print $2}')
MQTT_CONN_OK_SIGNAL=$(cat ${CONFIG} | grep -w mqttconnok | awk -F" = " '{print $2}')
MQTT_CONN_BAD_SIGNAL=$(cat ${CONFIG} | grep -w mqttconnbad | awk -F" = " '{print $2}')
MQTT_STATUS_OK_SIGNAL=$(cat ${CONFIG} | grep -w mqttstatusok | awk -F" = " '{print $2}')
DEVICE_UPFATE_SIGNAL=$(cat ${CONFIG} | grep -w deviceupdate | awk -F" = " '{print $2}')
WDT_ENABLE=$(cat ${CONFIG} | grep -w watchdog | awk -F" = " '{print $2}')

GET_TIMESTAMP=$(date "+%Y-%m-%d %H:%M:%S")
echo "${GET_TIMESTAMP}:zywlstart script start!" >> ${LOGFILE}

/bin/dmesg -n 1

#echo "*/10 * * * * /usr/sbin/ntpdate ntp.api.bz > /dev/null" > /var/spool/cron/crontabs/root
#service cron start

cp /root/ntp.conf /etc/

#timedatectl set-ntp no
#timedatectl
systemctl stop systemd-timesyncd
systemctl disable systemd-timesyncd
systemctl disable frpc

#set default dns
cat /etc/network/interfaces | grep -w "^dns-nameservers" > /dev/null
if [ $? -ne 0 ];then
	echo "dns-nameservers 114.114.114.114" >> /etc/network/interfaces
fi

ifconfig -a | grep eth0 > /dev/null
if [ $? -eq 0 ];then
	eth0macaddr=$(ifconfig eth0 | grep HWaddr | awk -F" " '{print $5}' | awk -F":" '{print $1$2$3$4$5$6}')
else
	eth0macaddr="1234567890ab"
fi
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
pppd_wait_count=0
gsmserial_status=0
network_status=0
sim_module_error=0
#mqtt_conn_status=0
monitor_close=0
mqtt_run_status=0
firmware_update_flag=0
pppd_not_have_online_func_count=0
mqtt_last_timestamp=0
exit_flag=0

thread_exit() {
	exit_flag=1
}

network_status_is_ok(){
	echo "network is ok" >> ${LOGFILE}
	network_status=1
}

network_status_is_bad(){
	echo "network is bad" >> ${LOGFILE}
	network_status=0
	#因为此时可能mqtt服务因为网络不同根本就没启动，所以需要在这里显示错误logo
	#这里不直接显示，为了防止多个显示程序被调用导致图片显示失败，所以这里假设mqtt曾经运行过
	mqtt_run_status=1
}

#sim module运行正常,可以启动pppd程序
gsmserial_status_is_ok() {
	echo "gsm serial is ok" >> ${LOGFILE}
	gsmserial_status=1
	sim_module_error=0
	systemctl stop zywlpppd
}
#sim module检测到没有sim card
gsm_sim_not_inserted() {
	systemctl stop zywlpppd
	echo "sim card not inserted" >> ${LOGFILE}
	sim_module_error=1
	gsmserial_status=0
	pppd_stop
}
#sim module检测到有sim卡，但是sim卡不能注册到网络
gsm_sim_module_error() {
	systemctl stop zywlpppd
	echo "sim card can't register!" >> ${LOGFILE}
	sim_module_error=1
	gsmserial_status=0
	pppd_stop
}

mqtt_connect_status_is_bad(){
#	mqtt_conn_status=0
	network_status=0
	systemctl restart zywlnet
	CUR_TIME=$(date "+%Y-%m-%d %H:%M:%S")
	echo "${CUR_TIME}:mqtt connect bad" >> ${LOGFILE}
}
mqtt_connect_status_is_ok(){
#mqtt_conn_status=1
	systemctl stop zywlnet
	mqtt_last_timestamp=$(get_system_timestamp)
	CUR_TIME=$(date "+%Y-%m-%d %H:%M:%S")
	echo "${CUR_TIME}:mqtt connect ok" >> ${LOGFILE}
}
mqtt_status_is_ok(){
	mqtt_last_timestamp=$(get_system_timestamp)
	#echo "mqtt thread is ok" >> ${LOGFILE}
}
device_will_update(){
	firmware_update_flag=1
	echo "i will update firmware" >> ${LOGFILE}
}

trap "thread_exit" ${EXIT_SIGNAL}
trap "gsmserial_status_is_ok" ${GSMSERIAL_SIGNAL}
trap "network_status_is_ok" ${NET_GOOD_SIGNAL}
trap "network_status_is_bad" ${NET_BAD_SIGNAL}
trap "gsm_sim_not_inserted" ${GSMSIMNOTINSERTED_SIGNAL}
trap "gsm_sim_module_error" ${GSMSIMMODULEERROR_SIGNAL}
trap "mqtt_connect_status_is_bad" ${MQTT_CONN_BAD_SIGNAL}
trap "mqtt_connect_status_is_ok" ${MQTT_CONN_OK_SIGNAL}
trap "mqtt_status_is_ok" ${MQTT_STATUS_OK_SIGNAL}
trap "device_will_update" ${DEVICE_UPFATE_SIGNAL}


#time_sync() {
#	ps -ef | grep ntpd | grep -v grep > /dev/null
#	if [ $? -ne 0 ];then
#		pid=$(ps -ef | grep update_time | grep -v grep | awk -F" " '{print $2}')
#		if [ -z "${pid}" ];then
#			service ntp start
#		fi  
#	fi  
#}

#monitor_thread_exit(){
#	pid=$(ps -ef | grep zywlmonitor | grep -v grep | awk -F" " '{print $2}')
#	if [ -n "${pid}" ];then
#		kill -${EXIT_SIGNAL} ${pid}
#		sleep 1
#	fi
#}
#
#monitor_thread_start(){
#	ps -ef | grep zywlmonitor | grep -v grep > /dev/null
#	if [ $? -ne 0 ];then
#		/root/zywlmonitor.sh $$ &
#	fi
#}

feed_watchdog(){
	if [ -f "/tmp/zywlwdt.pid" ];then
		pid=$(cat /tmp/zywlwdt.pid)
		if [ -n "${pid}" ];then
			kill -${FEEDWDT_SIGNAL} ${pid}
		else
			pid=$(ps -ef | grep feed | grep -v grep | awk -F" " '{print $2}')
			if [ -n "$pid" ];then
				echo ${pid} > /tmp/zywlwdt.pid
				kill -${FEEDWDT_SIGNAL} ${pid}
			fi
		fi	
	fi
}

get_system_timestamp(){
	echo $(date +%s)
}

if [ -f "${UPDATE_END}" ];then
	network_status=1
fi

if [ -f "${UPDATESTATUS}" ];then
	firmware_update_flag=1
else
	if [ "${WDT_ENABLE}" == "enable" ];then
		systemctl start zywlwdt
	fi
	python3 /root/showimage.py init
fi

curr_timestamp=$(get_system_timestamp)
mqtt_last_timestamp=${curr_timestamp}
wdt_timestamp=${curr_timestamp}
checktemp_timestamp=${curr_timestamp}
checkwpa_timestamp=${curr_timestamp}
checkppp_timestamp=${curr_timestamp}

systemctl start zywlnet

while true
do
	sleep 1
#	curr_timestamp=$(get_system_timestamp)
#	if [ ${exit_flag} -eq 1 ];then
#		if [ "${WDT_ENABLE}" == "enable" ];then
#			systemctl stop zywlwdt
#		fi
#		exit
#	fi

#	subval=$(expr ${curr_timestamp} - ${mqtt_last_timestamp})
#	#如果超过330秒没有接收到mqtt线程发来的signal,则认为mqtt程序中出现了异常。
#	if [ ${subval} -ge 360 ];then
#		mqtt_last_timestamp=${curr_timestamp}
#		CUR_TIME=$(date "+%Y-%m-%d %H:%M:%S") 
#		echo "${CUR_TIME}:check mqtt thread is ok" >> ${LOGFILE}
#		ps -ef | grep mqtt_client | grep -v grep > /dev/null
#		if [ $? -eq 0 ];then
#			feed_watchdog
#			echo "echo ${CUR_TIME}:mqtt thread need restart" >> ${LOGFILE}
#			systemctl restart zywlmqtt
#		fi
#	fi

#	if [ "${WDT_ENABLE}" == "enable" ];then
#		subval=$(expr ${curr_timestamp} - ${wdt_timestamp})
#		if [ ${subval} -ge 5 ];then
#			wdt_timestamp=${curr_timestamp}
#			#CUR_TIME=$(date "+%Y-%m-%d %H:%M:%S")
#			#echo "${CUR_TIME}:i feed the dog!" >> ${LOGFILE}
#			feed_watchdog
#		fi
#	fi

	subval=$(expr ${curr_timestamp} - ${checktemp_timestamp})
	if [ ${subval} -ge 300 ];then
		checktemp_timestamp=${curr_timestamp}
		temp=$(cat /sys/class/thermal/thermal_zone0/temp)
		CUR_TIME=$(date "+%Y-%m-%d %H:%M:%S")
		echo "${CUR_TIME}:current temp = ${temp}" >> /var/log/cputemplog
	fi

	subval=$(expr ${curr_timestamp} - ${checkwpa_timestamp})
	if [ ${subval} -ge 10 ]
	then
		checkwpa_timestamp=${curr_timestamp}
		ps -ef | grep wpa_supplicant | grep -v grep > /dev/null
		if [ $? -ne 0 ] 
		then 
			#equl 1 mean wpa thread not exists
			ssid=$(cat /root/net.conf | grep -w ssid | awk -F"=" '{print $2}')
			psk=$(cat /root/net.conf | grep -w psk | awk -F"=" '{print $2}')
			CUR_TIME=$(date "+%Y-%m-%d %H:%M:%S")
			echo "${CUR_TIME}:$0 wlan0 will start" >> ${LOGFILE}
			wpa_passphrase ${ssid} ${psk} > /etc/wpa.conf
			echo "ctrl_interface=/var/run/wpa_supplicant" >> /etc/wpa.conf
			sleep 0.2
			wpa_supplicant -iwlan0 -c /etc/wpa.conf > ${LOGFILE} 2>&1 &
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
		subval=$(expr ${curr_timestamp} - ${checkppp_timestamp})
		if [ ${subval} -ge 10 ];then
			checkppp_timestamp=${curr_timestamp}
			ps -ef | grep -w pppd | grep -v grep > /dev/null
			if [ $? -ne 0 ];then
				if [ ${gsmserial_status} -eq 1 ];then
					cat /dev/null > /var/log/ppplogfile
					${PPPD} call myapp &
				else
					feed_watchdog
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
					feed_watchdog
					pppd_stop
					systemctl start zywlpppd
				fi
				if [ ${pppd_not_have_online_func_count} -ge 3 ];then
					feed_watchdog
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
					systemctl stop zywlmqtt
					systemctl stop zywlwdt
					systemctl stop zywlnet
					ps -ef | grep update_firmware | grep -v grep > /dev/null
					if [ $? -ne 0 ]
					then
						/root/update_firmware.sh &
					fi
				else
					rm ${UPDATESTATUS}
					echo "update firmware: rm update_status file sta:${sta}" >> ${LOGFILE}
				fi
			else
				#如果UPDATESTATUS文件因为某些原因导致没有内容写入，那么就删除该文件
				rm ${UPDATESTATUS}
				echo "update firmware: rm update_status file sta is null" >> ${LOGFILE}
			fi
#			for var in $(systemctl list-unit-files | grep \.service | awk '{print $1}')
#				ret=$(systemctl status $var 2>&1 | grep "changed on disk")
		else
			firmware_update_flag=0
			if [ "${WDT_ENABLE}" == "enable" ];then
				systemctl start zywlwdt
			fi
		fi
	fi

	if [ ${network_status} -eq 1 ];then
		if [ ${mqtt_run_status} -eq 0 ];then
			mqtt_run_status=1
			feed_watchdog
			curr_timestamp=$(get_system_timestamp)
			mqtt_last_timestamp=${curr_timestamp}
			wdt_timestamp=${curr_timestamp}
			checktemp_timestamp=${curr_timestamp}
			checkwpa_timestamp=${curr_timestamp}
			checkppp_timestamp=${curr_timestamp}
			systemctl restart zywlmqtt
		fi
	else
		if [ ${mqtt_run_status} -eq 1 ];then
			mqtt_run_status=0
			feed_watchdog
			systemctl stop zywlmqtt
			python3 /root/showimage.py error
		fi
	fi  
done

