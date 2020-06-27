#!/bin/sh

while true
do
	r=$(ps -ef | grep test_pthread | grep -v grep)
	echo ${r}
	sleep 2
done
