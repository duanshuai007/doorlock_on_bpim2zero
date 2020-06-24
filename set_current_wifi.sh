#!/bin/bash
#该脚本用于调试使用，用来方便的设置的Wi-Fi，该脚本会更新net.conf中的ssid和psk信息
#ssid 就是wifi名
#psk 就是wifi密码
if [ $# -lt 2 ]
then
	echo "./set_current_wifi.sh ssid psk"
	exit
fi

sed -i "s/\(ssid=\).*/\1$1/" net.conf
sed -i "s/\(psk=\).*/\1$2/" net.conf
