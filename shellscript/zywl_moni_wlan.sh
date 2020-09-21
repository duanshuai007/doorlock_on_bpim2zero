#!/bin/bash

#
#	该脚本用来监视并配置wlan0的连接
#

NETFILE="/root/net.conf"
LOGFILE="/var/log/monitor.log"
SIGFIL="/root/signal.conf"

moni_main_pid=$1
EXIT_SIGNAL=$(cat ${SIGFIL} | grep -w SCRIPTEXIT | awk -F"=" '{print $2}')
WLAN_GOOD_SIG=$(cat ${SIGFIL} | grep -w WLANGOODSIG | awk -F"=" '{print $2}')
WLAN_BAD_SIG=$(cat ${SIGFIL} | grep -w WLANBADSIG | awk -F"=" '{print $2}')
wlan_conn_status=0

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
WLAN0_RULE=2

dhclient_wlan0() {
	pid=$(ps -ef | grep "dhclient wlan0" | grep -v grep | awk -F" " '{print $2}')
	if [ -n "${pid}" ]
	then
		kill ${pid} > /dev/null
		kill -9 ${pid} > /dev/null
	fi
	dhclient wlan0
}

get_net_ipaddr() {
	net=$1
	ipaddr=$(ip addr | grep ${net} | grep inet | awk -F" " '{print $2}' | awk -F"/" '{print $1}')
	echo ${ipaddr}
}

delete_iprule() {
	while true
	do
		ip rule delete lookup $1 > /dev/null
		if [ $? -ne 0 ]
		then
			break
		fi
	done
}

exit_flag=0

get_kill() {
	exit_flag=1
}

trap "get_kill" ${EXIT_SIGNAL}

echo "monitor wlan: main pid = ${moni_main_pid}" >> ${LOGFILE}
while true
do
	sleep 1

	if [ ${exit_flag} -eq 1 ]
	then
		ip route flush table ${WLAN0_RULE}
		#ip rule delete lookup ${WLAN0_RULE}
		delete_iprule ${WLAN0_RULE}
		exit
	fi	

	ip addr | grep wlan0 > /dev/null
	if [ $? -ne 0 ]
	then
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
				#iphead=$(ifconfig wlan0 | grep "inet addr" | awk -F" " '{print $2}' | awk -F":" '{print $2}' | awk -F"." '{print $1"\."$2"\."$3"\."}')
				iphead=$(ip addr | grep wlan0 | grep "inet" | awk -F" " '{print $2}' | awk -F"/" '{print $1}' | awk -F"." '{print $1"\."$2"\."$3"\."}')
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

						ip=$(get_net_ipaddr wlan0)
						ip rule | grep "${ip}" > /dev/null
						if [ $? -ne 0 ] 
						then
							delete_iprule ${WLAN0_RULE}
							ip rule add from ${ip} table ${WLAN0_RULE}
						fi  

						ip route show table ${WLAN0_RULE} | grep "${ip}" > /dev/null
						if [ $? -ne 0 ] 
						then
							ip route flush table ${WLAN0_RULE}
							ip route add default via ${gateway} dev wlan0 src ${ip} table ${WLAN0_RULE}
						fi  

						ping ${TESTDNSSERVER} -I wlan0 -c 1 > /dev/null
						#ping成功则切换网络，否则放弃
						if [ $? -eq 0 ]
						then
							connect_flag=1
							error_count=0
							if [ ${wlan_conn_status} -eq 0 ];then
								wlan_conn_status=1
								kill -${WLAN_GOOD_SIG} ${moni_main_pid}
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
			if [ ${wlan_conn_status} -eq 1 ];then
				wlan_conn_status=0
				kill -${WLAN_BAD_SIG} ${moni_main_pid}
				GET_TIMESTAMP=$(date "+%Y-%m-%d %H:%M:%S")
				echo "${GET_TIMESTAMP}:wlan0 not find dhcp file" >> ${LOGFILE}
			fi	
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

			if [ ${connect_count} -ge 3 ]
			then
				connect_count=0
				error_count=0
				if [ ${wlan_conn_status} -eq 1 ];then
					wlan_conn_status=0
					kill -${WLAN_BAD_SIG} ${moni_main_pid}
					GET_TIMESTAMP=$(date "+%Y-%m-%d %H:%M:%S")
					echo "${GET_TIMESTAMP}:connect wlan allways failed" >> ${LOGFILE}
				fi
				dhclient wlan0 -r
			fi
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
		dhclient wlan0 -r
		if [ ${wlan_conn_status} -eq 1 ];then
			wlan_conn_status=0
			kill -${WLAN_BAD_SIG} ${moni_main_pid}
		fi
	fi

done
