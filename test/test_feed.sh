#!/bin/bash

pid=$(ps -ef | grep feed | grep -v grep | awk -F" " '{print $2}')

if [ "$1" == "s" ];then
	kill -34 ${pid}
elif [ "$1" == "f" ];then
	kill -42 ${pid}
fi
