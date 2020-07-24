#!/usr/bin/env python3
#-*- coding:utf-8 -*-

import watchdog
import time
import os

def feed_dog():
	#当前时间戳
	cuttimestamp = int(time.time())
	#检测网络连接状态的文件都时间戳
	filemodifytimestamp = int(os.stat("/tmp/network_timestamp").st_mtime)
	#监测文件时间戳大于等于当前时间，喂狗
	#print("currnet time:{} ,file time:{}".format(cuttimestamp, filemodifytimestamp))
	if (filemodifytimestamp >= cuttimestamp):
		watchdog.open()
		watchdog.feed()
	elif (filemodifytimestamp < cuttimestamp):
		#小于当前时间的话,需要考虑到设备联网后更新时间，所以
		#是当当前时间大于网络监测时间的10-20分钟以内的话，就不喂狗，这时会导致设备重启
		#否则就喂狗，因为可能是设备刚链接上网络同步了时间导致当前时间远远大于网络监测时间戳
		sub = cuttimestamp - filemodifytimestamp
		#print("sub={}".format(sub))
		if ((sub > (60 * 10)) and (sub < (60 * 20))):
			print("do not feed watchdog")
			pass
		else:
			watchdog.open()
			watchdog.feed()

if __name__ == "__main__":
	feed_dog()
