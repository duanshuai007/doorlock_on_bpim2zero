#!/bin/bash

#监控网络是否可用

#route del default wlan0
#route add default gw 192.168.200.252 wlan0
#wlan0通过dhclient -r,dhclient wlan0来获取新的路由信息
#ppp0通过route add default ppp0来设置路由信息
dat=$(date "+%Y%m%d")
LOGFILE=/var/log/monitor_network_${dat}.log
GET_TIMESTAMP=$(date "+%Y-%m-%d %H:%M:%S")

setDefaultRoute() {
	#dhclient -r
	GET_TIMESTAMP=$(date "+%Y-%m-%d %H:%M:%S")
	echo $1 > /tmp/current_network
	case $1 in
		"wlan0")
			echo "${GET_TIMESTAMP}:set wlan0 as default route" >> ${LOGFILE}
			route del default ppp0  > /dev/null 2>&1
			dhclient wlan0
			;;
		"ppp0")
			echo "${GET_TIMESTAMP}:set ppp0 as default route" >> ${LOGFILE}
			dhclient -r
			route add default ppp0
			;;
		*)
			echo "${GET_TIMESTAMP}:error paramters" >> ${LOGFILE}
			;;
	esac
	
	echo "nameserver 114.114.114.114" > /etc/resolv.conf
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

CURRENT_NET=$(cat /root/net.conf | grep choice |  awk -F"=" '{print $2}')
CONTINUE=0
fail_count=0
err_count=0
not_set_route=0
count=0
net_is_change=0
can_create_mqtt_thread=0
connect_wifi_time=0
net_is_connect=0
while true
do
	#check network is ok
	DEFAULT_NET=$(cat /root/net.conf | grep choice |  awk -F"=" '{print $2}')
	#debug  message need delete
	GET_TIMESTAMP=$(date "+%Y-%m-%d %H:%M:%S")
	#echo "${GET_TIMESTAMP}:current:${CURRENT_NET} default:${DEFAULT_NET}" >> ${LOGFILE}
	if [ "${CURRENT_NET}" != "${DEFAULT_NET}" ]
	then
		#当前网络不等于默认的网络
		CONTINUE=1
		case "${DEFAULT_NET}" in
			"wlan0")
				#检测默认网络是否可用，如果可用，择切换到默认网络
				if [ ${connect_wifi_time} -eq 0 ]
				then
					connect_wifi_time=1
					ssid=$(cat /root/net.conf | grep -w ssid | awk -F"=" '{print $2}')
					psk=$(cat /root/net.conf | grep -w psk | awk -F"=" '{print $2}')
					/root/connect_wifi.sh ${ssid} ${psk}
				elif [ ${connect_wifi_time} -ge 5 ]
				then
					connect_wifi_time=0
				else
					connect_wifi_time=$(expr ${connect_wifi_time} + 1)
				fi
				sta=$(wpa_cli -iwlan0 status | grep wpa_state | awk -F"=" '{print $2}')
				echo "${GET_TIMESTAMP}:sta = ${sta}" >> ${LOGFILE}
				if [ "${sta}" == "COMPLETED" ]
				then 
					#获取gateway
					#echo "" > /etc/resolv.conf
					dhclient -r
					dhclient wlan0
					if [ -f /run/resolvconf/interface/wlan0.dhclient ]
					then
						gateway=$(cat /run/resolvconf/interface/wlan0.dhclient | grep -w nameserver | awk -F" " '{print $2}')
						#gateway=$(cat /etc/resolv.conf | grep -w nameserver | awk -F" " '{print $2}')
						#if [ -z "${gateway}" ] 
						#then
						#	gateway=$(cat /etc/resolv.conf | grep -w nameserver | awk -F"=" '{print $2}')
						#fi
						#获取到gateway后添加测试用的路由，进行ping测试
						if [ ! -z "${gateway}" ]
						then
							route add 114.114.114.114 gw ${gateway} wlan0
							sleep 1
							ping 114.114.114.114 -I wlan0 -c 1 > /dev/null
							#ping成功则切换网络，否则放弃
							if [ $? -eq 0 ]
							then 
								CURRENT_NET="wlan0"
								python3 /root/showimage.py 3
								setDefaultRoute wlan0
								fail_count=0
								net_is_change=1
								not_set_route=1
								net_is_connect=1
							else
								echo "ping failed" >> ${LOGFILE}
							fi
							route del 114.114.114.114 gw ${gateway} wlan0
						else
							echo "not find vaild gateway" >> ${LOGFILE}
						fi
					else
						echo "not find /run/resolvconf/interface/wlan0.dhclient " >> ${LOGFILE}
					fi
				fi
				;;
			"ppp0")
				#检测默认网络是否可用，如果可用，择切换到默认网络
				route add 114.114.114.114 ppp0
				sleep 1
				ping 114.114.114.114 -I ppp0 -c 1 > /dev/null
				#ping成功则切换网络，否则放弃
				if [ $? -eq 0 ]
				then
					CURRENT_NET="ppp0"
					python3 /root/showimage.py 3
					setDefaultRoute ppp0
					fail_count=0
					net_is_change=1
					not_set_route=1
					net_is_connect=1
				fi
				route del 114.114.114.114 ppp0
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
					CONTINUE=1
					if [ ${not_set_route} -eq 0 ]
					then	
						echo "${GET_TIMESTAMP}:wlan0 state is COMPLETED" >> ${LOGFILE}
						not_set_route=1
						python3 /root/showimage.py 3
						setDefaultRoute wlan0
						fail_count=0
						net_is_change=1
						net_is_connect=1
					fi
				else
					echo "${GET_TIMESTAMP}:wlan0 state is not COMPLETED" >> ${LOGFILE}
					CONTINUE=0
				fi
				;;
			"ppp0")
				CONTINUE=1
				#echo "${GET_TIMESTAMP}:set ppp0 default route" >> ${LOGFILE}
				if [ ${not_set_route} -eq 0 ]
				then 
					not_set_route=1
					python3 /root/showimage.py 3
					setDefaultRoute ppp0
					fail_count=0
					net_is_change=1
					net_is_connect=1
				fi
				;;
			*)
				sleep 5
				continue
				;;
		esac
	fi

	if [ ${CONTINUE} -eq 0 ]
	then
		err_count=$(expr ${err_count} + 1)
		if [ ${err_count} -ge 5 ]
		then
			#wifi连接不上，超时后设置ppp0连接
			GET_TIMESTAMP=$(date "+%Y-%m-%d %H:%M:%S")
			echo "${GET_TIMESTAMP}:${CURRENT_NET} connect error ${err_count}" >> ${LOGFILE}
			err_count=0
			not_set_route=0
			net_is_connect=0
			python3 /root/showimage.py 2
			if [ "${CURRENT_NET}" == "wlan0" ] 
			then
				setDefaultRoute ppp0
				CURRENT_NET="ppp0"
				net_is_change=1
			else
				setDefaultRoute wlan0
				CURRENT_NET="wlan0"
				net_is_change=1
			fi
		fi
	
		sleep 5
		continue
	fi

	if [ ${net_is_connect} -eq 1 ]
	then
		if [ ${count} -ge 6 ]
		then
			count=0
			#traceroute www.baidu.com > /dev/null 2>&1
			ping www.baidu.com -c 1 > /dev/null
			if [ $? -eq 0 ]
			then
				#equl 0 mean network is fine
				#echo 0 > /dev/null	
				fail_count=0
			else
				fail_count=$(expr ${fail_count} + 1)
				if [ ${fail_count} -ge 3 ]
				then
					fail_count=0
					net_is_connect=0
					GET_TIMESTAMP=$(date "+%Y-%m-%d %H:%M:%S")
					echo "${GET_TIMESTAMP}:network[${CURRENT_NET}] is bad, now change network" >> ${LOGFILE}
					python3 /root/showimage.py 2
					if [ "${CURRENT_NET}" == "wlan0" ]
					then
						CURRENT_NET="ppp0"
						setDefaultRoute ppp0
						net_is_change=1
					elif [ "${CURRENT_NET}" == "ppp0" ]
					then
						CURRENT_NET="wlan0"
						setDefaultRoute wlan0
						net_is_change=1
					fi
				fi
			fi
		fi
	fi

	if [ ${net_is_change} -eq 1 ]
	then
		fail_count=0
		echo "" > /tmp/netstatus
		GET_TIMESTAMP=$(date "+%Y-%m-%d %H:%M:%S")
		echo "${GET_TIMESTAMP}:net is change, kill old thread and restart" >> ${LOGFILE}
		pid=$(ps -ef | grep mqtt_client | grep -v grep | awk -F" " '{print $2}')
		echo "pid = ${pid}" >> ${LOGFILE}
		if [ ! -z "${pid}" ]
		then
			echo "kill ${pid}" >> ${LOGFILE}
			kill -9 ${pid}
			sleep 1
		fi
		can_create_mqtt_thread=1
		#mac=$(cat /tmp/eth0macaddr)
		#python3 /root/mqtt_client.py ${mac} &
		net_is_change=0
	fi

	if [ ${can_create_mqtt_thread} -eq 1 ]
	then 
		ping baidu.com -c 1 > /dev/null
		if [ $? -eq 0 ]
		then
			can_create_mqtt_thread=0
			echo "OK" > /tmp/netstatus
		fi
	fi

	count=$(expr ${count} + 1)
	sleep 2
done
