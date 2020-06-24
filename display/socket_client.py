#!/usr/bin/env python3
#-*- coding:utf-8 -*-

import threading
import socket
import time
import os
import sys
import struct
import LoggingQueue

class socket_client():

	server = None;

	def __init__(self):
		self.log = LoggingQueue.LoggingProducer().getlogger()
		self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

	def connect_to_server(self, port):
		try:
			self.server.connect(('127.0.0.1', port))
			return True
		except Exception as e:
			self.log.error("connect_to_server error:{}".format(e))
			return False

	'''
	等待发送的数据是list，每个list包含160个值，共有160个这样的子list
	'''
	def send_image_buffer(self, img:list)->bool:
		try:
			if self.server is None:
				self.log.error("server is None")
				return False
			btotal = bytes()
			for l in img:
				btotal += bytes(l)
			self.server.send(btotal)
			return True
		except Exception as e:
			self.log.error("send_image_buffer error:{}".format(e))
			return False

	def send_cmd(self, cmd:str)->bool:
		try:
			if self.server is None:
				self.log.error("server is None")
				return False
			sendbytes = bytes(cmd, encoding="utf-8")
			self.server.send(sendbytes)
		except Exception as e:
			self.log.error("send_cmd error:{}".format(e))
			return False
			

if __name__ == "__main__":
	s = socket_client()
	s.connect_to_server(8899)
	image = [1,2,3,4,5,6,7,8,9,0]
	s.send_image_buffer(image)
