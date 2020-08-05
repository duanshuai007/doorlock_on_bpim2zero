#!/bin/bash
#该脚本用于调试使用，用来方便的设置的Wi-Fi，该脚本会更新net.conf中的ssid和psk信息
#ssid 就是wifi名
#psk 就是wifi密码

NETFILE="/root/net.conf"

set_netconf_option() {
	case $1 in
		"choice")
		if [ $# -lt 2 ]
		then
			echo "run like this:"
			echo "./set_current_wifi.sh choice wlan0/ppp0/eth0"
			exit
		fi
		sed -i "s/\(choice=\).*/\1$2/"	${NETFILE}
		;;
		"wlan")
		if [ $# -lt 3 ]
		then
			echo "run like this:"
			echo "./set_current_wifi.sh wlan ssid psk"
			exit
		fi
		sed -i "s/\(ssid=\).*/\1$2/"	${NETFILE}
		sed -i "s/\(psk=\).*/\1$3/"		${NETFILE}
		;;
		*)
		;;
	esac
}

set_netconf_option $@
