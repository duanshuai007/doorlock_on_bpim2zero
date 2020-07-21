#!/bin/bash

#监控网络是否可用
#只要当该进程重启时才会根据日期创建新的log文件

#route del default wlan0
#route add default gw 192.168.200.252 wlan0
#wlan0通过dhclient -r,dhclient wlan0来获取新的路由信息
#ppp0通过route add default ppp0来设置路由信息
NETFILE="/root/net.conf"
LOGFILE="/var/log/monitor.log"
NETSTAT="/root/netstatus"
CURRENTNET="/tmp/current_network"
NETTIMESTAMP="/tmp/network_timestamp"

cat /dev/null > ${NETSTAT}

ETHSTATUS="/tmp/eth0status"
WLANSTATUS="/tmp/wlan0status"
PPPSTATUS="/tmp/ppp0status"

setDefaultRoute() {
	GET_TIMESTAMP=$(date "+%Y-%m-%d %H:%M:%S")
	echo $1 > /tmp/current_network
	dhclient -r
	case $1 in
		"wlan0")
			echo "${GET_TIMESTAMP}:set wlan0 as default route" >> ${LOGFILE}
			route del default ppp0  > /dev/null 2>&1
			dhclient wlan0
			;;
		"ppp0")
			echo "${GET_TIMESTAMP}:set ppp0 as default route" >> ${LOGFILE}
			route add default ppp0
			;;
		"eth0")
			echo "${GET_TIMESTAMP}:set eth0 as default route" >> ${LOGFILE}
			route del default ppp0  > /dev/null 2>&1
			dhclient eth0
			;;
		*)
			echo "${GET_TIMESTAMP}:error paramters" >> ${LOGFILE}
			;;
	esac
	
	echo "nameserver 114.114.114.114" > /etc/resolv.conf
}

kill_mqtt_thread() {
	GET_TIMESTAMP=$(date "+%Y-%m-%d %H:%M:%S")
	echo "${GET_TIMESTAMP}:net is change, kill old thread and restart" >> ${LOGFILE}
	pid=$(ps -ef | grep "mqtt" | grep -v grep | awk -F" " '{print $2}')
	echo "${GET_TIMESTAMP}:pid = ${pid}" >> ${LOGFILE}
	if [ ! -z "${pid}" ]
	then
		echo "${GET_TIMESTAMP}:kill ${pid}" >> ${LOGFILE}
		kill ${pid} > /dev/null
		kill -9 ${pid} > /dev/null
		sleep 1
	fi
}

monitor_network() {
	pid=$(ps -ef | grep zywl_moni_eth | grep -v grep | wc -l)
	if [ -n "${pid}" ]
		then
		if [ ${pid} -ge 3 ]
		then
			kill ${pid} > /dev/null
			kill -9 ${pid} > /dev/null
		elif [ ${pid} -eq 0 ]
		then
			/root/zywl_moni_eth.sh &
		fi
	fi

	pid=$(ps -ef | grep zywl_moni_wlan | grep -v grep | wc -l)
	if [ -n "${pid}" ]
	then
		if [ ${pid} -ge 3 ]
		then
			kill ${pid} > /dev/null
			kill -9 ${pid} > /dev/null
		elif [ ${pid} -eq 0 ]
		then
			/root/zywl_moni_wlan.sh &
		fi
	fi

	pid=$(ps -ef | grep zywl_moni_ppp | grep -v grep | wc -l)
	if [ -n "${pid}" ]
	then
		if [ ${pid} -ge 3 ]
		then
			kill ${pid} > /dev/null
			kill -9 ${pid} > /dev/null
		elif [ ${pid} -eq 0 ]
		then
			/root/zywl_moni_ppp.sh &
		fi
	fi
}

time_sync() {
	ps -ef | grep ntpd | grep -v grep > /dev/null
	if [ $? -ne 0 ]
	then
		pid=$(ps -ef | grep update_time.sh | grep -v grep | awk -F" " '{print $2}')
		if [ -z "${pid}" ]
		then
			service ntp start
		fi
	fi
}

read_netstatus() {
	case $1 in
		"wlan0")
		net_state=$(cat ${WLANSTATUS})
		;;
		"eth0")
		net_state=$(cat ${ETHSTATUS})
		;;
		"ppp0")
		net_state=$(cat ${PPPSTATUS})
		;;
		*)
		;;
	esac
}

DEFAULT_NET=$(cat ${NETFILE} | grep choice |  awk -F"=" '{print $2}')
if [ -f ${CURRENTNET} ]
then
	CURRENT_NET=$(cat ${CURRENTNET})
	if [ -z "${CURRENT_NET}" ]
	then
		CURRENT_NET=${DEFAULT_NET}
	fi
else
	CURRENT_NET=${DEFAULT_NET}
fi

count=0
net_state=0
fail_count=0
default_net_is_ok=0

while true
do
	monitor_network
	time_sync

	#系统启动时会从配置文件net.conf中读取默认配置的网络并进行连接
	if [ ${count} -ge 5 ]
	then
		count=0
		
		DEFAULT_NET=$(cat ${NETFILE} | grep choice |  awk -F"=" '{print $2}')
	
		read_netstatus ${DEFAULT_NET}
		if [ "${net_state}" == "OK" ]
		then
			default_net_is_ok=$(expr ${default_net_is_ok} + 1)
			if [ ${default_net_is_ok} -ge 3 ]
			then
				default_net_is_ok=0
				if [ "${DEFAULT_NET}" != "${CURRENT_NET}" ]
				then
					CURRENT_NET=${DEFAULT_NET}
					cat /dev/null > ${NETSTAT}
				fi
			fi
		else
			default_net_is_ok=0
			read_netstatus ${CURRENT_NET}
		fi

		GET_TIMESTAMP=$(date "+%Y-%m-%d %H:%M:%S")
		#echo "${GET_TIMESTAMP}:network[${CURRENT_NET}] status=${net_state}" >> ${LOGFILE}
		if [ "${net_state}" == "OK" ]
		then
			#equl 0 mean network is fine
			fail_count=0
			echo 0 > ${NETTIMESTAMP}
			sta=$(cat ${NETSTAT})
			if [ -z "${sta}" ]
			then
				kill_mqtt_thread
				setDefaultRoute ${CURRENT_NET}
				python3 /root/showimage.py 3
				echo "OK" > ${NETSTAT}
				echo ${CURRENT_NET} > ${CURRENTNET}
				/root/update_time.sh &
			fi
		else
			fail_count=$(expr ${fail_count} + 1)
			if [ ${fail_count} -ge 3 ]
			then
				fail_count=0
				GET_TIMESTAMP=$(date "+%Y-%m-%d %H:%M:%S")
				echo "${GET_TIMESTAMP}:network[${CURRENT_NET}] is bad, now change network" >> ${LOGFILE}
				python3 /root/showimage.py 2
				if [ "${CURRENT_NET}" == "eth0" ]
				then
					CURRENT_NET="wlan0"
				elif [ "${CURRENT_NET}" == "wlan0" ]
				then
					CURRENT_NET="ppp0"
				elif [ "${CURRENT_NET}" == "ppp0" ]
				then
					CURRENT_NET="eth0"
				fi
				#delete default route
				net=$(route -n | awk -F" " '{if($1=="0.0.0.0") print $8}')	
				if [ -n "${net}" ]
				then
					if [ "${net}" == "ppp0" ]
					then
						route del default ppp0
					else
						gw=$(route -n | awk -F" " '{if($1=="0.0.0.0") print $2}')
						route del default gw ${gw} ${net}
					fi
					cat /dev/null > ${NETSTAT}
				fi
			fi
		fi
	fi

	count=$(expr ${count} + 1)
	sleep 1
done
