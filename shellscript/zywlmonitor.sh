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

setCurrentRoute() {
	GET_TIMESTAMP=$(date "+%Y-%m-%d %H:%M:%S")
	echo $1 > /tmp/current_network
	echo "${GET_TIMESTAMP}:set $1 as current route" >> ${LOGFILE}
	dhclient -r
	case $1 in
		"wlan0")
			route del default ppp0  > /dev/null 2>&1
			dhclient wlan0
			;;
		"ppp0")
			route add default ppp0
			;;
		"eth0")
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
	#echo "${GET_TIMESTAMP}:net is change, kill old thread and restart" >> ${LOGFILE}
	pid=$(ps -ef | grep "mqtt" | grep -v grep | awk -F" " '{print $2}')
	echo "${GET_TIMESTAMP}:kill_mqtt_thread pid = ${pid}" >> ${LOGFILE}
	if [ ! -z "${pid}" ]
	then
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
		netsta=$(cat ${WLANSTATUS})
		;;
		"eth0")
		netsta=$(cat ${ETHSTATUS})
		;;
		"ppp0")
		netsta=$(cat ${PPPSTATUS})
		;;
		*)
		;;
	esac
	
	echo "${netsta}"
}

#获取一个可用的网络
get_vaild_network() {
	sta=$(cat ${ETHSTATUS})
	if [ "${sta}" == "OK" ]
	then
		echo "eth0"
		return
	fi
	sta=$(cat ${WLANSTATUS})
	if [ "${sta}" == "OK" ]
	then
		echo "wlan0"
		return
	fi
	sta=$(cat ${PPPSTATUS})
	if [ "${sta}" == "OK" ]
	then
		echo "ppp0"
		return
	fi
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
network_is_bad=0

GET_TIMESTAMP=$(date "+%Y-%m-%d %H:%M:%S")
echo "${GET_TIMESTAMP}:zywlmonitor script start!" >> ${LOGFILE}

while true
do
	monitor_network
	time_sync

	#系统启动时会从配置文件net.conf中读取默认配置的网络并进行连接
	if [ ${count} -ge 5 ]
	then
		count=0
		
		DEFAULT_NET=$(cat ${NETFILE} | grep choice |  awk -F"=" '{print $2}')
	
		net_state=$(read_netstatus ${DEFAULT_NET})
		if [ "${net_state}" == "OK" ]
		then
			default_net_is_ok=$(expr ${default_net_is_ok} + 1)
			if [ ${default_net_is_ok} -ge 3 ]
			then
				default_net_is_ok=0
				if [ "${DEFAULT_NET}" != "${CURRENT_NET}" ]
				then
					GET_TIMESTAMP=$(date "+%Y-%m-%d %H:%M:%S")
					echo "${GET_TIMESTAMP}: cur net not equl default net, from ${CURRENT_NET} change to ${DEFAULT_NET}" >> ${LOGFILE}
					CURRENT_NET=${DEFAULT_NET}
					cat /dev/null > ${NETSTAT}
				fi
			fi
		else
			default_net_is_ok=0
			net_state=$(read_netstatus ${CURRENT_NET})
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
				#kill_mqtt_thread
				setCurrentRoute ${CURRENT_NET}
				if [ ${network_is_bad} -eq 1 ]
				then
					python3 /root/showimage.py 3
					network_is_bad=0
				fi
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
				echo "${GET_TIMESTAMP}:network[${CURRENT_NET}] is bad" >> ${LOGFILE}
				vail_net=$(get_vaild_network)
				kill_mqtt_thread
				if [ -n "${vail_net}" ]
				then
					#发现其他可用的网络，切换到可用网络
					echo "${GET_TIMESTAMP}:find vaild network[${vail_net}], switch" >> ${LOGFILE}
					CURRENT_NET=${vail_net}
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
				else
					network_is_bad=1
					echo "${GET_TIMESTAMP}:not find vaild network" >> ${LOGFILE}
					python3 /root/showimage.py 2
					cat /dev/null > ${NETSTAT}
				fi
			fi
		fi
	fi

	count=$(expr ${count} + 1)
	sleep 1
done
