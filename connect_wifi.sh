#!/bin/bash

SSID=$1
PASSWORD=$2

if [ -z "${SSID}" -o -z "${PASSWORD}" ]
then
	echo "parameters error"
	echo "please run script like this:"
	echo "./script.sh ssid password"
	exit
fi

np=$(wpa_cli -iwlan0 add_n)
#该指令会根据网络列表中的个数自动递增，因为没有配置wpa.con文件，所以默认是0

#该指令设置Wifi名
wpa_cli -iwlan0 set_n ${np} ssid \"${SSID}\"

#设置Wifi密码
wpa_cli -iwlan0 set_n ${np} psk \"${PASSWORD}\"

#启动wifi
wpa_cli -iwlan0 select_n ${np}
wpa_cli -iwlan0 enable_n ${np}
