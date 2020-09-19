#!/bin/bash

#监控网络是否可用
#只要当该进程重启时才会根据日期创建新的log文件

#route del default wlan0
#route add default gw 192.168.200.252 wlan0
#wlan0通过dhclient -r,dhclient wlan0来获取新的路由信息
#ppp0通过route add default ppp0来设置路由信息
NETFILE="/root/net.conf"
LOGFILE="/var/log/zywllog"
CURRENTNET="/tmp/current_network"
SIGFIL="/root/signal.conf"
CONFIG="/root/config.ini"

start_pid=$1
wifi_enable=0
eth_enable=0
sim_enable=0

cat ${CONFIG} | grep -w wifi | grep -w enable > /dev/null
if [ $? -eq 0 ];then
	echo "wifi enable" >> ${LOGFILE}
	wifi_enable=1
	WLAN_GOOD_SIG=$(cat ${SIGFIL} | grep -w WLANGOODSIG | awk -F"=" '{print $2}')
	WLAN_BAD_SIG=$(cat ${SIGFIL} | grep -w WLANBADSIG | awk -F"=" '{print $2}')
fi

cat ${CONFIG} | grep -w eth | grep -w enable > /dev/null
if [ $? -eq 0 ];then
	echo "eth enable" >> ${LOGFILE}
	eth_enable=1
	ETH_GOOD_SIG=$(cat ${SIGFIL} | grep -w ETHGOODSIG | awk -F"=" '{print $2}')
	ETH_BAD_SIG=$(cat ${SIGFIL} | grep -w ETHBADSIG | awk -F"=" '{print $2}')
fi

cat ${CONFIG} | grep  -w sim | grep -w enable > /dev/null
if [ $? -eq 0 ];then
	echo "ppp enable" >> ${LOGFILE}
	sim_enable=1
	PPP_GOOD_SIG=$(cat ${SIGFIL} | grep -w PPPGOODSIG | awk -F"=" '{print $2}')
	PPP_BAD_SIG=$(cat ${SIGFIL} | grep -w PPPBADSIG | awk -F"=" '{print $2}')
fi

EXIT_SIGNAL=$(cat ${SIGFIL} | grep -w SCRIPTEXIT | awk -F"=" '{print $2}')
NET_GOOD_SIG=$(cat ${SIGFIL} | grep -w NETWORKOK | awk -F"=" '{print $2}')

count=0
net_state=0
default_net_is_ok=0
network_status=0
network_is_bad=0
network_count=0
eth0_network_status=0
wlan0_network_status=0
ppp0_network_status=0
exit_flag=0

get_gateway() {
	net=$1
	if [ -f /run/resolvconf/interface/${net}.dhclient ]
	then	
		#iphead=$(ifconfig ${net} | grep "inet addr" | awk -F" " '{print $2}' | awk -F":" '{print $2}' | awk -F"." '{print $1"\."$2"\."$3"\."}')
		iphead=$(ip addr | grep ${net} | grep inet | awk -F" " '{print $2}' | awk -F"/" '{print $1}' | awk -F"." '{print $1"\."$2"\."$3"\."}')
		if [ -n "iphead" ]
		then 
			gateway=$(cat /run/resolvconf/interface/${net}.dhclient | grep -w nameserver | grep "${iphead}" | awk -F" " '{print $2}')
			echo ${gateway}
			return
		fi
	fi
	echo ""
}

get_ip() {
	echo $(ip ad | grep $1 | grep inet | awk -F" " '{print $2}' | awk -F"/" '{print $1}')
}

setCurrentRoute() {
	ip=$(get_ip $1)
	echo $1:${ip} > ${CURRENTNET}
	GET_TIMESTAMP=$(date "+%Y-%m-%d %H:%M:%S")
	echo "${GET_TIMESTAMP}:set $1 as current route" >> ${LOGFILE}
	errcount=0
	add_ppp_errcount=0
	while true
	do
		route del default
		case $1 in
			"wlan0")
				;&
			"eth0")
				gw=$(get_gateway $1)
				route add default gw ${gw} $1
				;;
			"ppp0")
				route add default ppp0
				if [ $? -ne 0 ];then
					add_ppp_errcount=$(expr ${add_ppp_errcount} + 1)
					if [ ${add_ppp_errcount} -ge 3 ];then
						ppp0_network_status=0
						break
					fi
				fi
				;;
			*)
				echo "${GET_TIMESTAMP}:error paramters" >> ${LOGFILE}
				;;
		esac
		#cur_default_route=$(route -n | awk '{if($1=="0.0.0.0") print($8)}')
		cur_default_route=$(ip route | grep default | awk -F" " '{print $5}')
		if [ "${cur_default_route}" == "$1" ]
		then
			break
		fi
		errcount=$(expr ${errcount} + 1)
		if [ ${errcount} -ge 3 ];then
			break
		fi
		sleep 0.5
	done
#echo "nameserver 114.114.114.114" > /etc/resolv.conf
}

wlan_monitor_thread_status=0
eth_monitor_thread_status=0
ppp_monitor_thread_status=0

monitor_network() {
	if [ ${eth_enable} -eq 1 ];then
		if [ ${eth_monitor_thread_status} -eq 0 ];then
			ps -ef | grep zywl_moni_eth | grep -v grep > /dev/null
			if [ $? -ne 0 ];then
				eth_monitor_thread_status=1
				/root/zywl_moni_eth.sh $$ &
			fi
		fi
	fi

	if [ ${wifi_enable} -eq 1 ];then
		if [ ${wlan_monitor_thread_status} -eq 0 ];then
			ps -ef | grep zywl_moni_wlan | grep -v grep > /dev/null
			if [ $? -ne 0 ];then
				wlan_monitor_thread_status=1
				/root/zywl_moni_wlan.sh $$ &
			fi
		fi
	fi

	if [ ${sim_enable} -eq 1 ];then
		if [ ${ppp_monitor_thread_status} -eq 0 ];then
			ps -ef | grep zywl_moni_ppp | grep -v grep > /dev/null
			if [ $? -ne 0 ];then
				ppp_monitor_thread_status=1
				/root/zywl_moni_ppp.sh $$ &
			fi
		fi
	fi
}

donot_monitor_network() {
	if [ ${eth_enable} -eq 1 ];then
		pid=$(ps -ef | grep zywl_moni_eth | grep -v grep | awk '{print $2}')
		if [ -n "${pid}" ]
		then
			kill -${EXIT_SIGNAL} ${pid}  > /dev/null
		fi
	fi

	if [ ${wifi_enable} -eq 1 ];then
		pid=$(ps -ef | grep zywl_moni_wlan | grep -v grep | awk '{print $2}')
		if [ -n "${pid}" ]
		then
			kill -${EXIT_SIGNAL} ${pid}  > /dev/null
		fi
	fi

	if [ ${sim_enable} -eq 1 ];then
		pid=$(ps -ef | grep zywl_moni_ppp | grep -v grep | awk '{print $2}')
		if [ -n "${pid}" ]
		then
			kill -${EXIT_SIGNAL} ${pid}  > /dev/null
		fi
	fi
}

GET_TIMESTAMP=$(date "+%Y-%m-%d %H:%M:%S")
echo "${GET_TIMESTAMP}:zywlmonitor script start!" >> ${LOGFILE}

eth0_network_status_is_bad(){
	echo "eth0 status bad" >> ${LOGFILE}
	eth0_network_status=0
}
eth0_network_status_is_good(){
	echo "eth0 status good" >> ${LOGFILE}
	eth0_network_status=1
}
if [ ${eth_enable} -eq 1 ];then
	trap "eth0_network_status_is_bad" ${ETH_BAD_SIG}
	trap "eth0_network_status_is_good" ${ETH_GOOD_SIG}
fi

wlan0_network_status_is_bad(){
	echo "wlan0 status bad" >> ${LOGFILE}
	wlan0_network_status=0
}
wlan0_network_status_is_good(){
	echo "wlan0 status good" >> ${LOGFILE}
	wlan0_network_status=1
}
if [ ${wifi_enable} -eq 1 ];then
	trap "wlan0_network_status_is_bad" ${WLAN_BAD_SIG}
	trap "wlan0_network_status_is_good" ${WLAN_GOOD_SIG}
fi

ppp0_network_status_is_bad(){
	echo "ppp0 status bad" >> ${LOGFILE}
	ppp0_network_status=0
}
ppp0_network_status_is_good(){
	echo "ppp0 status good" >> ${LOGFILE}
	ppp0_network_status=1
}
if [ ${sim_enable} -eq 1 ];then
	trap "ppp0_network_status_is_bad" ${PPP_BAD_SIG}
	trap "ppp0_network_status_is_good" ${PPP_GOOD_SIG}
fi

thread_exit(){
	exit_flag=1
}

trap "thread_exit" ${EXIT_SIGNAL}

get_netstatus() {
	case $1 in
		"wlan0")
		netsta=${wlan0_network_status}
		;;
		"eth0")
		netsta=${eth0_network_status}
		;;
		"ppp0")
		netsta=${ppp0_network_status}
		;;
		*)
		netsta=0
		;;
	esac
	
	echo ${netsta}
}

#获取一个可用的网络
get_vaild_network() {
	if [ ${eth0_network_status} -eq 1 ];then
		echo "eth0"
		return
	fi
	if [ ${wlan0_network_status} -eq 1 ];then
		echo "wlan0"
		return
	fi
	if [ ${ppp0_network_status} -eq 1 ];then
		echo "ppp0"
		return
	fi
}

CURRENT_NET=$(cat ${NETFILE} | grep choice |  awk -F"=" '{print $2}')

while true
do
	if [ ${exit_flag} -eq 1 ];then
		donot_monitor_network
		GET_TIMESTAMP=$(date "+%Y-%m-%d %H:%M:%S")
		echo "${GET_TIMESTAMP}:monitor script exit now!" >> ${LOGFILE}
		sync
		exit
	fi

	monitor_network

	#系统启动时会从配置文件net.conf中读取默认配置的网络并进行连接
	if [ ${count} -ge 2 ]
	then
		count=0
		
		net_state=$(get_netstatus ${CURRENT_NET})
		if [ ${net_state} -eq 1 ];then
			#equl 1 mean network is fine
			if [ ${network_status} -eq 0 ];then
				network_status=1
				setCurrentRoute ${CURRENT_NET}
				if [ ${network_is_bad} -eq 1 ]
				then
					python3 /root/showimage.py logo
					network_is_bad=0
				fi
				kill -${NET_GOOD_SIG} ${start_pid}
			else
				#用来处理默认路由因为某种情况被错误的删除
				#net=$(route -n | awk -F" " '{if($1=="0.0.0.0") print $8}')
				#if [ -z "${net}" ]
				ip route | grep default > /dev/null
				if [ $? -ne 0 ];then
					#如果没能发现默认的路由信息，则添加默认路由
					setCurrentRoute ${CURRENT_NET}
					kill -${NET_GOOD_SIG} ${start_pid}
				fi
			fi
		else
			network_status=0
			GET_TIMESTAMP=$(date "+%Y-%m-%d %H:%M:%S")
			echo "${GET_TIMESTAMP}:network[${CURRENT_NET}] is bad" >> ${LOGFILE}
			vail_net=$(get_vaild_network)
			if [ -n "${vail_net}" ]
			then
				network_count=0
				#发现其他可用的网络，切换到可用网络
				echo "${GET_TIMESTAMP}:find vaild network[${vail_net}], switch" >> ${LOGFILE}
				CURRENT_NET=${vail_net}
				#delete default route
				#net=$(route -n | awk -F" " '{if($1=="0.0.0.0") print $8}')	
				ip route | grep default > /dev/null
				if [ $? -eq 0 ];then
					route del default
				fi
			else
				network_count=$(expr ${network_count} + 1)
				if [ ${network_count} -ge 10 ];then
					network_count=0
					if [ ${network_is_bad} -eq 0 ];then
						network_is_bad=1
						echo "${GET_TIMESTAMP}:not find vaild network" >> ${LOGFILE}
						python3 /root/showimage.py error
					fi
				fi
			fi
		fi
	fi

	count=$(expr ${count} + 1)
	sleep 1
done
