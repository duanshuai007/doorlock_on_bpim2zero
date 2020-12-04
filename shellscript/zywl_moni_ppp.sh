#!/bin/bash

#
#	监视ppp网络状态
#
PPPLOGFILE="/var/log/ppplogfile"
TESTDNSSERVER="8.8.8.8"
LOGFILE="/var/log/monitor.log"
SIGFIL="/root/signal.conf"

PPP0_RULE=3
error_count=0
ppp_connect_status=0

moni_main_pid=$1
EXIT_SIGNAL=$(cat ${SIGFIL} | grep -w SCRIPTEXIT | awk -F"=" '{print $2}')
PPP_GOOD_SIG=$(cat ${SIGFIL} | grep -w PPPGOODSIG | awk -F"=" '{print $2}')
PPP_BAD_SIG=$(cat ${SIGFIL} | grep -w PPPBADSIG | awk -F"=" '{print $2}')

pppd_stop() {
	pid=$(ps -ef | grep pppd | grep -v grep | awk -F" " '{print $2}')
	if [ -n "${pid}" ]
	then
		kill -INT ${pid}
	fi  
}

get_net_ipaddr() {
	net=$1
	ipaddr=$(ip addr | grep ${net} | grep inet | awk -F" " '{print $2}')
	echo ${ipaddr}
}

delete_iprule() {
	while true
	do
		ip rule delete lookup $1
		sleep 0.2 
		ip rule | grep "lookup $1" > /dev/null
		if [ $? -ne 0 ];then
			break
		fi  
	done
}

exit_flag=0
get_kill() {
	exit_flag=1
}

trap "get_kill" ${EXIT_SIGNAL}

echo "monitor ppp: main pid = ${moni_main_pid}" >> ${LOGFILE}
while true
do
	sleep 1
	if [ ${exit_flag} -eq 1 ]
	then
		ip route flush table ${PPP0_RULE}
		#ip rule delete lookup ${PPP0_RULE}
		delete_iprule ${PPP0_RULE}
		exit
	fi

	ip addr | grep ppp0 > /dev/null
	if [ $? -ne 0 ]
	then
		continue
	fi

	ifconfig ppp0 | grep RUNNING > /dev/null
	if [ $? -ne 0 ]
	then
		if [ ${ppp_connect_status} -eq 1 ];then
			ppp_connect_status=0
			error_count=0
			GET_TIMESTAMP=$(date "+%Y-%m-%d %H:%M:%S")
			echo "${GET_TIMESTAMP}:find ppp0 is not running" >> ${LOGFILE}
			kill -${PPP_BAD_SIG} ${moni_main_pid}
		fi
		continue
	fi

	cat ${PPPLOGFILE} | grep "Serial connection established" > /dev/null
	if [ $? -ne 0 ]
	then
		#not find this string，mean pppd run wrong
		if [ ${ppp_connect_status} -eq 1 ];then
			ppp_connect_status=0
			kill -${PPP_BAD_SIG} ${moni_main_pid}
		fi
	else
		route -n | grep ${TESTDNSSERVER} | grep ppp0 > /dev/null
		if [ $? -ne 0 ]
		then
			route add ${TESTDNSSERVER} ppp0
			sleep 1
		fi
		
		ip=$(get_net_ipaddr ppp0)
		ip rule | grep "${ip}" > /dev/null
		if [ $? -ne 0 ] 
		then
			delete_iprule ${PPP0_RULE}
			ip rule add from ${ip} table ${PPP0_RULE}
		fi  

		ip route show table ${PPP0_RULE} | grep "${ip}" > /dev/null
		if [ $? -ne 0 ] 
		then
			ip route flush table ${PPP0_RULE}
			ip route add default via 0.0.0.0 dev ppp0 src ${ip} table ${PPP0_RULE}
		fi
		
		#GET_TIMESTAMP=$(date "+%Y-%m-%d %H:%M:%S")
		#echo "${GET_TIMESTAMP}:ppp ping test" >> ${LOGFILE}
		ping ${TESTDNSSERVER} -I ppp0 -c 1 > /dev/null
		if [ $? -eq 0 ]
		then
			error_count=0
			if [ ${ppp_connect_status} -eq 0 ];then
				ppp_connect_status=1
				kill -${PPP_GOOD_SIG} ${moni_main_pid}
			fi
		else
			error_count=$(expr ${error_count} + 1)
			if [ ${error_count} -ge 3 ]
			then
				error_count=0
				pppd_stop
				if [ ${ppp_connect_status} -eq 1 ];then
					ppp_connect_status=0
					kill -${PPP_BAD_SIG} ${moni_main_pid}
				fi
			fi
		fi
	fi
done
