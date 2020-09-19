#!/bin/bash

get_system_timestamp(){
	current=`date "+%Y-%m-%d %H:%M:%S"`
	echo $(date -d "${current}" +%s)
}

t=$(get_system_timestamp)

sleep 3

t1=$(get_system_timestamp)

s=$(expr ${t1} - ${t})
echo $s
