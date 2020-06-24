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

#np=$(wpa_cli -iwlan0 add_n)
np=0	
#该指令会根据网络列表中的个数自动递增，因为没有配置wpa.con文件，所以默认是0
wpa_cli -iwlan0 disable_n ${np} > /dev/null 2>&1
#该指令设置Wifi名
wpa_cli -iwlan0 set_n ${np} ssid \"${SSID}\" > /dev/null 2>&1

#设置Wifi密码
wpa_cli -iwlan0 set_n ${np} psk \"${PASSWORD}\" > /dev/null 2>&1

#启动wifi
wpa_cli -iwlan0 select_n ${np} > /dev/null 2>&1
wpa_cli -iwlan0 enable_n ${np} > /dev/null 2>&1
