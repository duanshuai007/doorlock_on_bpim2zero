#!/bin/bash

#
#	监视eth网络状态
#	

LOGFILE="/var/log/monitor.log"
SIGFIL="/root/signal.conf"

moni_main_pid=$1
EXIT_SIGNAL=$(cat ${SIGFIL} | grep -w SCRIPTEXIT | awk -F"=" '{print $2}')
ETH_GOOD_SIG=$(cat ${SIGFIL} | grep -w ETHGOODSIG | awk -F"=" '{print $2}')
ETH_BAD_SIG=$(cat ${SIGFIL} | grep -w ETHBADSIG | awk -F"=" '{print $2}')

start_dhcp_time=0
cycle_time=0
#用来使网络在第一次链接上的时候快速进行route和dhcp等操作而不必等待cycle_time>10
connect_flag=0
#用于错误缓冲，这样就不会因为偶尔的一次失败而认为整个网络是错误的
error_count=0
TESTDNSSERVER="119.29.29.29"
ETH0_RULE=1

dhclient_eth0() {
	pid=$(ps -ef | grep "dhclient eth0" | grep -v grep | awk -F" " '{print $2}')
	if [ -n "${pid}" ]
	then
		kill ${pid} > /dev/null
		kill -9 ${pid} > /dev/null
	fi
	dhclient eth0
}

get_net_ipaddr() {
	net=$1
	ipaddr=$(ifconfig ${net} | grep "inet addr" | awk -F" " '{print $2}' | awk -F":" '{print $2}')
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
connect_status=0

get_kill() {
	exit_flag=1
}

trap "get_kill" ${EXIT_SIGNAL}

echo "monitor eth: main pid = ${moni_main_pid}" >> ${LOGFILE}
while true
do
	sleep 1
	if [ ${exit_flag} -eq 1 ]
	then
		ip route flush table ${ETH0_RULE}
		ip rule delete lookup ${ETH0_RULE}
		exit
	fi

	ifconfig eth0 | grep RUNNING > /dev/null
	if [ $? -ne 0 ]
	then
		if [ ${connect_status} -eq 1 ];then
			connect_status=0
			cycle_time=0
			start_dhcp_time=0
			connect_flag=0
			error_count=0
			kill -${ETH_BAD_SIG} ${moni_main_pid}
			GET_TIMESTAMP=$(date "+%Y-%m-%d %H:%M:%S")
			echo "${GET_TIMESTAMP}:find eth0 is not running" >> ${LOGFILE}
		fi
		continue
	fi
	
	cycle_time=$(expr ${cycle_time} + 1)

	if [ -f /run/resolvconf/interface/eth0.dhclient ]
	then
		if [ ${cycle_time} -ge 10 -o ${connect_flag} -eq 0 ]
		then
			cycle_time=0
			start_dhcp_time=0
			#iphead=$(ifconfig eth0 | grep "inet addr" | awk -F" " '{print $2}' | awk -F":" '{print $2}' | awk -F"." '{print $1"\."$2"\."$3"\."}')
			iphead=$(ip ad | grep wlan0 | grep "inet" | awk -F" " '{print $2}' | awk -F"/" '{print $1}' | awk -F"." '{print $1"\."$2"\."$3"\."}')
			if [ -n "${iphead}" ]
			then
				gateway=$(cat /run/resolvconf/interface/eth0.dhclient | grep -w nameserver | grep "${iphead}" | awk -F" " '{print $2}')
				if [ -n "${gateway}" ]
				then
					route -n | grep eth0 | grep ${TESTDNSSERVER} > /dev/null
					if [ $? -ne 0 ]
					then
						#若没有test网关
						route add ${TESTDNSSERVER} gw ${gateway} eth0
						sleep 1
					else    
						#发现test网关
						route -n | grep eth0 | grep ${TESTDNSSERVER} | grep ${gateway} > /dev/null
						if [ $? -ne 0 ]
						then
							#test网管不是这个网络gateway的网关
							oldgw=$(route -n | grep eth0 | grep ${TESTDNSSERVER} | awk '{print $2}')
							route del ${TESTDNSSERVER} gw ${oldgw} eth0
							sleep 0.5 
							route add ${TESTDNSSERVER} gw ${gateway} eth0
							sleep 1
						fi      
					fi  
				
					ip=$(get_net_ipaddr eth0)
					ip rule | grep "${ip}" > /dev/null
					if [ $? -ne 0 ]
					then
						delete_iprule ${ETH0_RULE}
						ip rule add from ${ip} table ${ETH0_RULE}
					fi

					ip route show table ${ETH0_RULE} | grep "${ip}" > /dev/null
					if [ $? -ne 0 ]
					then
						ip route flush table ${ETH0_RULE}
						ip route add default via ${gateway} dev eth0 src ${ip} table ${ETH0_RULE}
					fi

					ping ${TESTDNSSERVER} -I eth0 -c 1 > /dev/null
					if [ $? -eq 0 ]
					then
						connect_flag=1
						error_count=0
						if [ ${connect_status} -eq 0 ];then
							connect_status=1
							kill -${ETH_GOOD_SIG} ${moni_main_pid}
						fi
					else
						GET_TIMESTAMP=$(date "+%Y-%m-%d %H:%M:%S")
						echo "${GET_TIMESTAMP}:eth0 ping failed" >> ${LOGFILE}
						connect_flag=0
						error_count=$(expr ${error_count} + 1)
					fi
				else
					GET_TIMESTAMP=$(date "+%Y-%m-%d %H:%M:%S")
					echo "${GET_TIMESTAMP}:eth0 not find vaild gateway" >> ${LOGFILE}
					connect_flag=0
					error_count=$(expr ${error_count} + 1)
				fi
			else
				GET_TIMESTAMP=$(date "+%Y-%m-%d %H:%M:%S")
				echo "${GET_TIMESTAMP}:eth0 not find vaild ipaddress" >> ${LOGFILE}
				connect_flag=0
				error_count=$(expr ${error_count} + 1)
			fi
		fi
	else
		connect_flag=0
		if [ ${connect_status} -eq 1 ];then
			connect_status=0
			kill -${ETH_BAD_SIG} ${moni_main_pid}
		fi
		if [ ${start_dhcp_time} -eq 0 ]
		then
			ip addr flush dev eth0
			dhclient_eth0 &
		fi

		start_dhcp_time=$(expr ${start_dhcp_time} + 1)
		if [ ${start_dhcp_time} -ge 20 ] #every 2 seconds, mul 10 equl 20 seconds
		then
			start_dhcp_time=0
		fi	
	fi

	if [ ${error_count} -ge 5 ]
	then
		error_count=0
		dhclient eth0 -r
		if [ ${connect_status} -eq 1 ];then
			connect_status=0
			kill -${ETH_BAD_SIG} ${moni_main_pid}
		fi
	fi   
done
