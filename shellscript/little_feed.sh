#!/bin/bash

python3 /home/watchdog/feed.py
while true
do
	sleep 5
	python3 /home/watchdog/feed.py
done
