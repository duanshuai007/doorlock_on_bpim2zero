#!/bin/bash

#
#	该脚本用来监视并配置wlan0的连接
#

NETFILE="/root/net.conf"
STATUSFILE="/tmp/wlan0status"
LOGFILE="/var/log/monitor.log"
CURRENT_NET="/tmp/current_network"

connect_wifi_time=0
start_dhcp=0
start_dhcp_time=0
cycle_time=0
#用来使网络在第一次链接上的时候快速进行route和dhcp等操作而不必等待cycle_time>10
connect_flag=0
#用于错误缓冲，这样就不会因为偶尔的一次失败而认为整个网络是错误的
error_count=0
connect_count=0
TESTDNSSERVER="114.114.114.114"

dhclient_wlan0() {
	pid=$(ps -ef | grep "dhclient wlan0" | grep -v grep | awk -F" " '{print $2}')
	if [ -n "${pid}" ]
	then
		kill ${pid} > /dev/null
		kill -9 ${pid} > /dev/null
	fi
	dhclient wlan0
}

touch ${STATUSFILE}

while true
do
	sleep 1
#curnet=$(cat ${CURRENT_NET})
#	defnet=$(cat ${NETFILE} | grep choice | awk -F"=" '{print $2}')

	ifconfig -a | grep wlan0 > /dev/null
	if [ $? -ne 0 ]
	then
		continue
	fi

	ifconfig wlan0 | grep RUNNING > /dev/null
	if [ $? -ne 0 ]
	then
		sta=$(cat ${STATUSFILE})
		if [ -n "${sta}" ]
		then
			connect_count=0
			connect_wifi_time=0
			start_dhcp=0
			start_dhcp_time=0
			cycle_time=0
			connect_flag=0
			error_count=0
			cat /dev/null > ${STATUSFILE}
			GET_TIMESTAMP=$(date "+%Y-%m-%d %H:%M:%S")
			echo "${GET_TIMESTAMP}:find wlan0 is not running" >> ${LOGFILE}
		fi
		continue
	fi

	sta=$(wpa_cli -iwlan0 status | grep wpa_state | awk -F"=" '{print $2}')
	if [ "${sta}" == "COMPLETED" ]
	then
		connect_count=0
		if [ -f /run/resolvconf/interface/wlan0.dhclient ]
		then
			cycle_time=$(expr ${cycle_time} + 1)
			if [ ${cycle_time} -ge 10 -o ${connect_flag} -eq 0 ]
			then
				cycle_time=0
				start_dhcp=0
				start_dhcp_time=0
				iphead=$(ifconfig wlan0 | grep "inet addr" | awk -F" " '{print $2}' | awk -F":" '{print $2}' | awk -F"." '{print $1"\."$2"\."$3"\."}')
				if [ -n "${iphead}" ]
				then
					gateway=$(cat /run/resolvconf/interface/wlan0.dhclient | grep -w nameserver | grep "${iphead}" | awk -F" " '{print $2}')
					#获取到gateway后添加测试用的路由，进行ping测试
					if [ -n "${gateway}" ]
					then
						#route add 114.114.114.114 gw ${gateway} wlan0
						route -n | grep wlan0 | grep ${TESTDNSSERVER} > /dev/null
						if [ $? -ne 0 ]
						then
							#若没有114网关
							route add ${TESTDNSSERVER} gw ${gateway} wlan0
							sleep 1
						else
							#发现114网关
							route -n | grep wlan0 | grep ${TESTDNSSERVER} | grep ${gateway} > /dev/null
							if [ $? -ne 0 ]
							then
								#114网管不是这个网络gateway的网关
								oldgw=$(route -n | grep wlan0 | grep ${TESTDNSSERVER} | awk '{print $2}')
								route del ${TESTDNSSERVER} gw ${oldgw} wlan0
								sleep 0.5
								route add ${TESTDNSSERVER} gw ${gateway} wlan0	
								sleep 1
							fi
						fi

						ping ${TESTDNSSERVER} -I wlan0 -c 1 > /dev/null
						#ping成功则切换网络，否则放弃
						if [ $? -eq 0 ]
						then
							connect_flag=1
							error_count=0
							sta=$(cat ${STATUSFILE})
							if [ -z "${sta}" ]
							then
								echo "OK" > ${STATUSFILE}
							fi
						else
							GET_TIMESTAMP=$(date "+%Y-%m-%d %H:%M:%S")
							echo "${GET_TIMESTAMP}:wlan0 ping failed" >> ${LOGFILE}
							connect_flag=0
							error_count=$(expr ${error_count} + 1)
						fi
						#route del 114.114.114.114 gw ${gateway} wlan0
					else
						GET_TIMESTAMP=$(date "+%Y-%m-%d %H:%M:%S")
						echo "${GET_TIMESTAMP}:wlan0 not find vaild gateway" >> ${LOGFILE}
						connect_flag=0
						error_count=$(expr ${error_count} + 1)
					fi #if [ -n "${gateway}" ]
				else
					error_count=$(expr ${error_count} + 1)
					connect_flag=0
					GET_TIMESTAMP=$(date "+%Y-%m-%d %H:%M:%S")
					echo "${GET_TIMESTAMP}:not get vaild dns server" >> ${LOGFILE}
				fi #if [ -n "${iphead}" ]
			fi #if [ ${cycle_time} -ge 10 -o ${connect_flag} -eq 0 ]
		else #if [ -f /run/resolvconf/interface/wlan0.dhclient ]
			connect_flag=0
			sta=$(cat ${STATUSFILE})
			if [ -n "${sta}" ]
			then
				GET_TIMESTAMP=$(date "+%Y-%m-%d %H:%M:%S")
				echo "${GET_TIMESTAMP}:wlan0 not find dhcp file" >> ${LOGFILE}
			fi
			cat /dev/null > ${STATUSFILE}
			if [ ${start_dhcp} -eq 0 ] 
			then
				start_dhcp=1
				ip addr flush dev wlan0
				dhclient_wlan0 &
			else
				start_dhcp_time=$(expr ${start_dhcp_time} + 1)
				if [ ${start_dhcp_time} -ge 20 ] #every 1 seconds, mul 10 equl 20 seconds
				then
					start_dhcp_time=0
					start_dhcp=0
				fi  
			fi 
		fi
	else
		connect_flag=0
		if [ ${connect_wifi_time} -eq 0 ]
		then
			ssid=$(cat ${NETFILE} | grep -w ssid | awk -F"=" '{print $2}')
			psk=$(cat ${NETFILE} | grep -w psk | awk -F"=" '{print $2}')
			
			/root/connect_wifi.sh ${ssid} ${psk}
			connect_count=$(expr ${connect_count} + 1)
		fi

		connect_wifi_time=$(expr ${connect_wifi_time} + 1)
		if [ ${connect_wifi_time} -ge 10 ]
		then
			connect_wifi_time=0
		fi
	fi

	if [ ${error_count} -ge 5 ]
	then
		error_count=0
		cat /dev/null > ${STATUSFILE}
	fi
	if [ ${connect_count} -ge 3 ]
	then
		connect_count=0
		error_count=0
		sta=$(cat ${STATUSFILE})
		if [ -n "${sta}" ]
		then
			GET_TIMESTAMP=$(date "+%Y-%m-%d %H:%M:%S")
			echo "${GET_TIMESTAMP}:connect wlan allways failed" >> ${LOGFILE}
		fi
		cat /dev/null > ${STATUSFILE}
	fi

done
