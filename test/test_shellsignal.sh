#!/bin/bash

getsignal() {
	echo "get signal"
}

trap "getsignal" SIGRTMIN

while true
do
	sleep 1
	echo "pid=$$"
done
