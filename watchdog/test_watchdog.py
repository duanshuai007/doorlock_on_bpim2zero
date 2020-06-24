#!/usr/bin/env python3
#-*- coding:utf-8 -*-

import watchdog
import time

watchdog.open()
print("open!")
while True:
	watchdog.feed()
	time.sleep(1)
	print("feed!")
