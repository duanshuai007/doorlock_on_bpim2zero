#!/bin/bash

#监控网络是否可用
#只要当该进程重启时才会根据日期创建新的log文件

#route del default wlan0
#route add default gw 192.168.200.252 wlan0
#wlan0通过dhclient -r,dhclient wlan0来获取新的路由信息
#ppp0通过route add default ppp0来设置路由信息
dat=$(date "+%Y%m%d")
LOGFILE=/var/log/monitor_network_${dat}.log
GET_TIMESTAMP=$(date "+%Y-%m-%d %H:%M:%S")
NETSTAT=/root/netstatus
CURRENTNET=/tmp/current_network

cat /dev/null > ${NETSTAT}

fail_count=0
not_set_route=0
count=0
connect_wifi_time=0
start_dhcp=0
start_dhcp_time=0

run_dhclient() {
	case $1 in 
		"wlan0")
			pid=$(ps -ef | grep "dhclient wlan0" | grep -v grep | awk -F" " '{print $2}')
			if [ -n "${pid}" ]
			then
				kill -9 ${pid}
			fi
			dhclient wlan0
			;;
		"eth0")
			pid=$(ps -ef | grep "dhclient eth0" | grep -v grep | awk -F" " '{print $2}')
			if [ -n "${pid}" ]
			then
				kill -9 ${pid}
			fi
			dhclient eth0
			;;
		*)
			;;
	esac
}

setDefaultRoute() {
	GET_TIMESTAMP=$(date "+%Y-%m-%d %H:%M:%S")
	echo $1 > /tmp/current_network
	dhclient -r
	case $1 in
		"wlan0")
			echo "${GET_TIMESTAMP}:set wlan0 as default route" >> ${LOGFILE}
			route del default ppp0  > /dev/null 2>&1
			run_dhclient wlan0
			;;
		"ppp0")
			echo "${GET_TIMESTAMP}:set ppp0 as default route" >> ${LOGFILE}
			route add default ppp0
			;;
		"eth0")
			echo "${GET_TIMESTAMP}:set eth0 as default route" >> ${LOGFILE}
			route del default ppp0  > /dev/null 2>&1
			run_dhclient eth0
			;;
		*)
			echo "${GET_TIMESTAMP}:error paramters" >> ${LOGFILE}
			;;
	esac
	
	echo "nameserver 114.114.114.114" > /etc/resolv.conf
}

kill_mqtt_thread() {
	fail_count=0
	cat /dev/null > ${NETSTAT}
	GET_TIMESTAMP=$(date "+%Y-%m-%d %H:%M:%S")
	echo "${GET_TIMESTAMP}:net is change, kill old thread and restart" >> ${LOGFILE}
	pid=$(ps -ef | grep "mqtt" | grep -v grep | awk -F" " '{print $2}')
	echo "pid = ${pid}" >> ${LOGFILE}
	if [ ! -z "${pid}" ]
	then
		echo "kill ${pid}" >> ${LOGFILE}
		kill -9 ${pid}
		sleep 1
	fi
}

#cat /dev/null > ${LOGFILE}
#等待两个进程启动
fail_retry=0
ppp_fail=0
while true
do
	GET_TIMESTAMP=$(date "+%Y-%m-%d %H:%M:%S")
	ps -ef | grep pppd | grep -v grep > /dev/null
	if [ $? -ne 0 ]
	then 
		echo "${GET_TIMESTAMP}:pppd thread not exists" >> ${LOGFILE}
	else
		ps -ef | grep wpa_supplicant | grep -v grep > /dev/null
		if [ $? -ne 0 ]
		then 
			echo "${GET_TIMESTAMP}:wpa thread not exists!" >> ${LOGFILE}
		else
			break
		fi
	fi
	sleep 1
	fail_retry=$(expr ${fail_retry} + 1)
	if [ ${fail_retry} -ge 10 ]
	then
		ppp_fail=1
		break
	fi
done

#CURRENT_NET=$(cat /root/net.conf | grep choice |  awk -F"=" '{print $2}')
CURRENT_NET=$(cat /tmp/current_network)
if [ -z "${CURRENT_NET}" ]
then
	CURRENT_NET="eth0"
fi

while true
do
	#check network is ok
	DEFAULT_NET=$(cat /root/net.conf | grep choice |  awk -F"=" '{print $2}')
	#debug  message need delete
	GET_TIMESTAMP=$(date "+%Y-%m-%d %H:%M:%S")
	#echo "${GET_TIMESTAMP}:current:${CURRENT_NET} default:${DEFAULT_NET}" >> ${LOGFILE}

	ps -ef | grep ntpd | grep -v grep > /dev/null
	if [ $? -ne 0 ]
	then
		pid=$(ps -ef | grep update_time.sh | grep -v grep | awk -F" " '{print $2}')
		if [ -z "${pid}" ]
		then
			service ntp start
		fi
	fi

	if [ "${CURRENT_NET}" != "${DEFAULT_NET}" ]
	then
		#当前网络不等于默认的网络
		case "${DEFAULT_NET}" in
			"wlan0")
				#检测默认网络是否可用，如果可用，择切换到默认网络
				if [ ${connect_wifi_time} -eq 0 ]
				then
					ssid=$(cat /root/net.conf | grep -w ssid | awk -F"=" '{print $2}')
					psk=$(cat /root/net.conf | grep -w psk | awk -F"=" '{print $2}')
					echo "connect to wifi ssid:${ssid} psk:${psk}" >> ${LOGFILE}
					/root/connect_wifi.sh ${ssid} ${psk}
				fi

				connect_wifi_time=$(expr ${connect_wifi_time} + 1)
				if [ ${connect_wifi_time} -ge 5 ]
				then
					connect_wifi_time=0
				fi

				sta=$(wpa_cli -iwlan0 status | grep wpa_state | awk -F"=" '{print $2}')
				#echo "${GET_TIMESTAMP}:sta = ${sta}" >> ${LOGFILE}
				if [ "${sta}" == "COMPLETED" ]
				then 
					#获取gateway
					#echo "" > /etc/resolv.conf
					if [ ${start_dhcp} -eq 0 ]
					then
						start_dhcp=1
						ip addr flush dev wlan0
						run_dhclient wlan0 &
					else
						start_dhcp_time=$(expr ${start_dhcp_time} + 1)
						if [ ${start_dhcp_time} -ge 10 ] #every 2 seconds, mul 10 equl 20 seconds
						then
							start_dhcp_time=0
							start_dhcp=0
						fi
					fi

					if [ -f /run/resolvconf/interface/wlan0.dhclient ]
					then
						start_dhcp=0
						start_dhcp_time=0
						iphead=$(ifconfig wlan0 | grep "inet addr" | awk -F" " '{print $2}' | awk -F":" '{print $2}' | awk -F"." '{print $1"\."$2"\."$3"\."}')
						if [ -n "${iphead}" ]
						then 
							gateway=$(cat /run/resolvconf/interface/wlan0.dhclient | grep -w nameserver | grep "${iphead}" | awk -F" " '{print $2}')
							#获取到gateway后添加测试用的路由，进行ping测试
							if [ -n "${gateway}" ]
							then
								route add 114.114.114.114 gw ${gateway} wlan0
								sleep 1
								ping 114.114.114.114 -I wlan0 -c 1 > /dev/null
								#ping成功则切换网络，否则放弃
								if [ $? -eq 0 ]
								then 
									CURRENT_NET="wlan0"
									#python3 /root/showimage.py 3
									kill_mqtt_thread
									setDefaultRoute wlan0
									fail_count=0
									not_set_route=1
								else
									echo "wlan0 ping failed" >> ${LOGFILE}
								fi
								route del 114.114.114.114 gw ${gateway} wlan0
							else
								echo "wlan0 not find vaild gateway" >> ${LOGFILE}
							fi
						fi
					fi
				fi
				;;
			"ppp0")
				#检测默认网络是否可用，如果可用，择切换到默认网络
				ip addr flush dev ppp0
				route add 114.114.114.114 ppp0
				sleep 1
				ping 114.114.114.114 -I ppp0 -c 1 > /dev/null
				#ping成功则切换网络，否则放弃
				if [ $? -eq 0 ]
				then
					CURRENT_NET="ppp0"
					#python3 /root/showimage.py 3
					kill_mqtt_thread
					setDefaultRoute ppp0
					fail_count=0
					not_set_route=1
				fi
				route del 114.114.114.114 ppp0
				;;
			"eth0")
				if [ ${start_dhcp} -eq 0 ]
				then
					start_dhcp=1
					ip addr flush dev eth0
					run_dhclient eth0 &
				else
					start_dhcp_time=$(expr ${start_dhcp_time} + 1)
					if [ ${start_dhcp_time} -ge 10 ] #every 2 seconds, mul 10 equl 20 seconds
					then
						start_dhcp_time=0
						start_dhcp=0
					fi
				fi

				if [ -f /run/resolvconf/interface/eth0.dhclient ]
				then
					start_dhcp=0
					start_dhcp_time=0
					iphead=$(ifconfig eth0 | grep "inet addr" | awk -F" " '{print $2}' | awk -F":" '{print $2}' | awk -F"." '{print $1"\."$2"\."$3"\."}')
					if [ -n "${iphead}" ]
					then
						gateway=$(cat /run/resolvconf/interface/eth0.dhclient | grep -w nameserver | grep "${iphead}" | awk -F" " '{print $2}')
						if [ -n "${gateway}" ]
						then
							route add 114.114.114.114 gw ${gateway} eth0
							sleep 1
							ping 114.114.114.114 -I eth0 -c 1 > /dev/null
							if [ $? -eq 0 ]
							then
								CURRENT_NET="eth0"
								#python3 /root/showimage.py 3
								kill_mqtt_thread
								setDefaultRoute eth0
								fail_count=0
								not_set_route=1
							else
								echo "eth0 ping failed" >> ${LOGFILE}
							fi
							route del 114.114.114.114 gw ${gateway} eth0
						else
							echo "eth0 not find vaild gateway" >> ${LOGFILE}
						fi
					fi
				fi
				;;
			*)
				sleep 5
				continue
				;;
		esac
	else
		#当前网络等于默认网络
		GET_TIMESTAMP=$(date "+%Y-%m-%d %H:%M:%S")
		case "${DEFAULT_NET}" in
			"wlan0")
				#检查wifi连接是否成功
				sta=$(wpa_cli -iwlan0 status | grep wpa_state | awk -F"=" '{print $2}')	
				if [ "${sta}" == "COMPLETED" ]
				then 
					if [ ${not_set_route} -eq 0 ]
					then	
						echo "${GET_TIMESTAMP}:wlan0 state is COMPLETED" >> ${LOGFILE}
						not_set_route=1
						python3 /root/showimage.py 3
						kill_mqtt_thread
						setDefaultRoute wlan0
						fail_count=0
					fi
				else
					echo "${GET_TIMESTAMP}:wlan0 state is not COMPLETED" >> ${LOGFILE}
				fi
				;;
			"ppp0")
				#echo "${GET_TIMESTAMP}:set ppp0 default route" >> ${LOGFILE}
				if [ ${not_set_route} -eq 0 ]
				then 
					not_set_route=1
					python3 /root/showimage.py 3
					kill_mqtt_thread
					setDefaultRoute ppp0
					fail_count=0
				fi
				;;
			"eth0")
				if [ ${not_set_route} -eq 0 ]
				then 
					not_set_route=1
					python3 /root/showimage.py 3
					kill_mqtt_thread
					setDefaultRoute eth0
					fail_count=0
				fi
				;;
			*)
				sleep 5
				continue
				;;
		esac
	fi

	#系统启动时会从配置文件net.conf中读取默认配置的网络并进行连接
	if [ ${count} -ge 3 ]
	then
		count=0
		#traceroute www.baidu.com > /dev/null 2>&1
		ping www.baidu.com -I ${CURRENT_NET} -c 1 > /dev/null # 4 seconds
		if [ $? -eq 0 ]
		then
			#equl 0 mean network is fine
			fail_count=0
			sta=$(cat ${NETSTAT})
			if [ -z "${sta}" ]
			then
				python3 /root/showimage.py 3
				echo "OK" > ${NETSTAT}
				/root/update_time.sh &
				dat=$(date "+%Y%m%d")
				LOGFILE=/var/log/monitor_network_${dat}.log
			fi
		else
			fail_count=$(expr ${fail_count} + 1)
			if [ ${fail_count} -ge 3 ]
			then
				start_dhcp=0
				start_dhcp_time=0
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
				kill_mqtt_thread
				setDefaultRoute ${CURRENT_NET}
			fi
		fi
	fi

	count=$(expr ${count} + 1)
	sleep 2
done
