#!/bin/bash

#监控网络是否可用

#route del default wlan0

#route add default gw 192.168.200.252 wlan0
#wlan0通过dhclient -r,dhclient wlan0来获取新的路由信息
#ppp0通过route add default ppp0来设置路由信息

LOGFILE=/var/log/monitor_network.log
GET_TIMESTAMP=$(date "+%Y-%m-%d %H:%M:%S")

setDefaultRoute() {
	route del default ppp0  > /dev/null 2>&1
	dhclient -r
	GET_TIMESTAMP=$(date "+%Y-%m-%d %H:%M:%S")
	case $1 in
		"wlan0")
			echo "${GET_TIMESTAMP}:set wlan0 as default route" >> ${LOGFILE}
			dhclient wlan0
			;;
		"ppp0")
			echo "${GET_TIMESTAMP}:set ppp0 as default route" >> ${LOGFILE}
			route add default ppp0
			;;
		*)
			echo "${GET_TIMESTAMP}:error paramters" >> ${LOGFILE}
			;;
	esac
	
	echo "nameserver 114.114.114.114" > /etc/resolv.conf
}

cat /dev/null > ${LOGFILE}
#等待两个进程启动
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
	sleep 0.2
done

#echo "go on!!!!" >> ${LOGFILE}

CURRENT_NET=$(cat /root/net.conf | grep choice |  awk -F"=" '{print $2}')
#setDefaultRoute $DEF
#if [ "${CURRENT_NET}" == "ppp0" ]
#then
#	echo "${GET_TIMESTAMP}:set ppp0 to default" >> ${LOGFILE}
#	route del default ppp0  > /dev/null 2>&1
#	dhclient -r
#	echo "nameserver 114.114.114.114" > /etc/resolv.conf
#	route add default ppp0
#fi

CONTINUE=0
fail_count=0
err_count=0
not_set_route=0
while true
do
	#check network is ok
	DEFAULT_NET=$(cat /root/net.conf | grep choice |  awk -F"=" '{print $2}')
	#debug  message need delete
	echo "current:${CURRENT_NET} default:${DEFAULT_NET}"
	if [ "${CURRENT_NET}" != "${DEFAULT_NET}" ]
	then
		#当前网络不等于默认的网络
		CONTINUE=1
		case "${DEFAULT_NET}" in
			"wlan0")
				#检测默认网络是否可用，如果可用，择切换到默认网络
				sta=$(wpa_cli -iwlan0 status | grep wpa_state | awk -F"=" '{print $2}')
				if [ "${sta}" == "COMPLETED" ]
				then 
					#获取gateway
					dhclient -r
					dhclient wlan0 
					sleep 0.5
					gateway=$(cat /etc/resolv.conf | awk -F" " '{print $2}')
					if [ -z "${gateway}" ] 
					then
						gateway=$(cat /etc/resolv.conf | awk -F"=" '{print $2}')
					fi
					#获取到gateway后添加测试用的路由，进行ping测试
					if [ ! -z "${gateway}" ]
					then
						route add 114.114.114.114 gw ${gateway} wlan0
						sleep 1
						ping 114.114.114.114 -I wlan0 -c 10 > /dev/null
						#ping成功则切换网络，否则放弃
						if [ $? -eq 0 ]
						then 
							CURRENT_NET="wlan0"
							setDefaultRoute wlan0
							fail_count=0
						fi
					fi
				fi
				;;
			"ppp0")
				#检测默认网络是否可用，如果可用，择切换到默认网络
				ping 114.114.114.114 -I ppp0 -c 10 > /dev/null
				#ping成功则切换网络，否则放弃
				if [ $? -eq 0 ]
				then
					CURRENT_NET="ppp0"
					setDefaultRoute ppp0
					fail_count=0
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
					CONTINUE=1
					echo "${GET_TIMESTAMP}:wlan0 state is COMPLETED" >> ${LOGFILE}
					if [ ${not_set_route} -eq 0 ]
					then	
						not_set_route=1
						setDefaultRoute wlan0
						fail_count=0
					fi
				else
					echo "${GET_TIMESTAMP}:wlan0 state is not COMPLETED" >> ${LOGFILE}
					CONTINUE=0
				fi
				;;
			"ppp0")
				CONTINUE=1
				echo "${GET_TIMESTAMP}:set ppp0 default route" >> ${LOGFILE}
				if [ ${not_set_route} -eq 0 ]
				then 
					not_set_route=1
					setDefaultRoute ppp0
					fail_count=0
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
			if [ "${CURRENT_NET}" == "wlan0" ] 
			then
				setDefaultRoute ppp0
				CURRENT_NET="ppp0"
			else
				setDefaultRoute wlan0
				CURRENT_NET="wlan0"
			fi
		fi
	
		sleep 5
		continue
	fi

	#traceroute www.baidu.com > /dev/null 2>&1
	ping www.baidu.com -c 5 > /dev/null
	if [ $? -eq 0 ]
	then
		#equl 0 mean network is fine
		echo 0 > /dev/null	
	else
		fail_count=$(expr $fail_count + 1)
		if [ ${fail_count} -gt 5 ]
		then
			fail_count=0
			GET_TIMESTAMP=$(date "+%Y-%m-%d %H:%M:%S")
			echo "${GET_TIMESTAMP}:network[${CURRENT_NET}] is bad, now change network" >> ${LOGFILE}
			if [ "${CURRENT_NET}" == "wlan0" ]
			then
				CURRENT_NET="ppp0"
				setDefaultRoute ppp0
			elif [ "${CURRENT_NET}" == "ppp0" ]
			then
				CURRENT_NET="wlan0"
				setDefaultRoute wlan0
			fi
		fi
	fi

	sleep 20
done
