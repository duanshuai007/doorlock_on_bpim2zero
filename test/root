#!/usr/bin/env python3
#-*- coding:utf-8 -*-

import serial
import os
import sys
import time
import shutil
import threading
import signal
import config
import select
import queue
from threading import Timer

import LoggingQueue

class check_ttys2isok():

	uart = None

	def open_serial(self):
		self.uart = serial.Serial("/dev/ttyS2", 115200, 8, serial.PARITY_NONE, 1, 0.5)
		if self.uart is None:
			print("open ttyS2 failed")
			return False
		return True

	def __deal_with_response(self, response:str):
		try:	
			if "ERROR" in response or "OK" in response:
				return True
			else:
				return False
		except Exception as e:
			print("__deal_with_response error:{}".format(e))

	def send_atcmd_and_wait_response(self, atcmd:str, wait:int):
		strmsg = ""
		try:
			print("cmd:{}".format(atcmd))
			self.uart.write(bytes(atcmd.encode('utf-8')))
			curtime = int(time.time())
			timeout = curtime + wait
			while curtime < timeout:
				curtime = int(time.time())
				bmsg = self.uart.read(1024)
				if len(bmsg) != 0:
					strmsg += str(bmsg, encoding='utf-8')
					if strmsg.endswith('\r\n'):
						ret = self.__deal_with_response(strmsg)
						if ret == True:
							break
				time.sleep(0.1)
			return strmsg
		except Exception as e:
			print("send_atcmd_and_wait_response error:{}".format(e))
			return strmsg

if __name__ == "__main__":
	if len(sys.argv) < 3:
		print("paramters error")
		exit(1)
	cmd = sys.argv[1]
	wait = int(sys.argv[2])
	s = check_ttys2isok()
	if s.open_serial() == True:
		realcmd = "{}\r\n".format(cmd)
		print("response:{}".format(s.send_atcmd_and_wait_response(realcmd, wait)))
