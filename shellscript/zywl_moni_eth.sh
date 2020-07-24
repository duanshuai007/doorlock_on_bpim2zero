#!/bin/bash

#
#	监视eth网络状态
#	

NETFILE="/root/net.conf"
STATUSFILE="/tmp/eth0status"
CURRENT_NET="/tmp/current_network"
LOGFILE="/var/log/monitor.log"
start_dhcp_time=0
cycle_time=0
#用来使网络在第一次链接上的时候快速进行route和dhcp等操作而不必等待cycle_time>10
connect_flag=0
#用于错误缓冲，这样就不会因为偶尔的一次失败而认为整个网络是错误的
error_count=0
TESTDNSSERVER="119.29.29.29"

dhclient_eth0() {
	pid=$(ps -ef | grep "dhclient eth0" | grep -v grep | awk -F" " '{print $2}')
	if [ -n "${pid}" ]
	then
		kill ${pid} > /dev/null
		kill -9 ${pid} > /dev/null
	fi
	dhclient eth0
}

cat /dev/null > ${STATUSFILE}

while true
do
	sleep 1

	cycle_time=$(expr ${cycle_time} + 1)
	if [ -f /run/resolvconf/interface/eth0.dhclient ]
	then
		if [ ${cycle_time} -ge 10 -o ${connect_flag} -eq 0 ]
		then
			cycle_time=0
			start_dhcp_time=0
			iphead=$(ifconfig eth0 | grep "inet addr" | awk -F" " '{print $2}' | awk -F":" '{print $2}' | awk -F"." '{print $1"\."$2"\."$3"\."}')
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
				
					ping ${TESTDNSSERVER} -I eth0 -c 1 > /dev/null
					if [ $? -eq 0 ]
					then
						connect_flag=1
						error_count=0
						echo "OK" > ${STATUSFILE}
					else
						echo "eth0 ping failed" >> ${LOGFILE}
						connect_flag=0
						error_count=$(expr ${error_count} + 1)
					fi
				else
					echo "eth0 not find vaild gateway" >> ${LOGFILE}
					connect_flag=0
					error_count=$(expr ${error_count} + 1)
				fi
			else
				echo "eth0 not find vaild ipaddress" >> ${LOGFILE}
				connect_flag=0
				error_count=$(expr ${error_count} + 1)
			fi
		fi
	else
		connect_flag=0
		cat /dev/null > ${STATUSFILE}
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
		cat /dev/null > ${STATUSFILE}
	fi   
done
