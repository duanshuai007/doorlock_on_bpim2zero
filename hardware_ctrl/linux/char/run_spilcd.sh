#!/bin/bash

func() {
	pid=$(ps -ef | grep -w spilcd_ctrl | grep -v grep | awk -F" " '{print $2}')
	if [ -n "${pid}" ]
	then
		kill -9 ${pid}
	fi
	port=$(cat /root/config.ini | grep SOCKETPORT | awk -F"=" '{print $2}')
	/root/display/spilcd_ctrl  ${port} &
}

func
