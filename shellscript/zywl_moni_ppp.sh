#!/bin/bash

#
#	监视ppp网络状态
#
STATEFILE="/tmp/ppp0status"
PPPLOGFILE="/var/log/ppplogfile"
TESTDNSSERVER="8.8.8.8"
LOGFILE="/var/log/monitor.log"
PPP0_RULE=3

error_count=0
ping_count=0

pppd_stop() {
	pid=$(ps -ef | grep pppd | grep -v grep | awk -F" " '{print $2}')
	if [ -n "${pid}" ]
	then
		kill -INT ${pid}
	fi  
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


touch ${STATEFILE}

while true
do
	sleep 5

	ifconfig -a | grep ppp0 > /dev/null
	if [ $? -ne 0 ]
	then
		continue
	fi

	ifconfig ppp0 | grep RUNNING > /dev/null
	if [ $? -ne 0 ]
	then
		sta=$(cat ${STATEFILE})
		if [ -n "${sta}" ]
		then
			error_count=0
			GET_TIMESTAMP=$(date "+%Y-%m-%d %H:%M:%S")
			echo "${GET_TIMESTAMP}:find ppp0 is not running" >> ${LOGFILE}
			cat /dev/null > ${STATEFILE}
		fi
		continue
	fi

	cat ${PPPLOGFILE} | grep "Serial connection established" > /dev/null
	if [ $? -ne 0 ]
	then
		#not find this string，mean pppd run wrong
		cat /dev/null > ${STATEFILE}
	else
		route -n | grep ${TESTDNSSERVER} | grep ppp0 > /dev/null
		if [ $? -ne 0 ]
		then
			route add ${TESTDNSSERVER} ppp0
			sleep 1
		fi
		
		sta=$(cat ${STATEFILE})
		if [ -n "${sta}" ]
		then
			ping_count=$(expr ${ping_count} + 1)
			if [ ${ping_count} -lt 12 ]
			then
				continue
			fi
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
		
		ping_count=0
		GET_TIMESTAMP=$(date "+%Y-%m-%d %H:%M:%S")
		echo "${GET_TIMESTAMP}:ppp ping test" >> ${LOGFILE}
		ping ${TESTDNSSERVER} -I ppp0 -c 1 > /dev/null
		if [ $? -eq 0 ]
		then
			error_count=0
			echo "OK" > ${STATEFILE}
		else
			error_count=$(expr ${error_count} + 1)
			if [ ${error_count} -ge 3 ]
			then
				error_count=0
				pppd_stop
				cat /dev/null > ${STATEFILE}
			fi
		fi
	fi
done
