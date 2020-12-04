#!/usr/bin/env python3
#-*- coding:utf-8 -*-


import sys
import os
import logging
import ssl
import paho.mqtt.client as mqtt
import queue
import threading
import time
import json
import random
import struct

class mqtt_client(mqtt.Client):

	#debug = True
	username = None
	password = None
	logger = None
	
	sub_topic_list = []
	delete_list = []

	gpio_handler = None
	gpio_group = None
	gpio_pin = None


	lcd_logopic_160x20 = [

		255,255,255,255,255,255,255,255,255,255,255,255,255,255,255,255,255,255,255,255,
		255,255,255,255,255,255,255,255,255,255,255,255,255,255,255,255,255,255,255,255,
		255,255,255,255,255,255,255,255,255,255,255,255,255,255,255,255,255,255,255,255,
		255,255,255,255,255,255,255,255,255,254,127,255,255,255,255,255,255,255,255,255,
		255,255,255,255,255,255,255,255,255,252,63,255,255,255,255,255,255,255,255,255,
		255,255,255,255,255,255,255,255,255,252,63,255,255,255,255,255,255,255,255,255,
		255,255,255,255,255,255,255,255,255,252,63,255,199,255,255,255,255,255,255,255,
		255,255,255,255,255,255,255,255,255,252,63,255,199,255,255,255,255,255,255,255,
		255,255,255,255,255,255,248,255,255,252,63,255,135,255,255,255,255,255,255,255,
		255,255,255,255,255,255,248,255,255,156,63,255,135,255,255,255,255,255,255,255,
		255,255,255,255,255,255,248,127,255,12,63,255,135,254,127,255,255,255,255,255,
		255,255,255,255,255,255,248,127,255,14,127,255,143,252,63,255,255,255,255,255,
		255,255,255,255,255,255,252,127,255,15,249,255,15,252,63,255,255,255,255,255,
		255,255,255,255,255,255,255,255,255,143,240,255,14,120,127,255,255,255,255,255,
		255,255,255,255,255,255,255,255,255,143,240,255,12,56,127,255,255,255,255,255,
		255,255,255,255,255,255,255,255,255,223,241,255,28,120,255,255,255,255,255,255,
		255,255,255,255,255,255,255,255,255,255,241,254,24,127,255,255,255,255,255,255,
		255,255,255,255,255,255,255,255,255,255,241,254,24,127,255,255,255,255,255,255,
		255,255,255,255,255,255,231,223,255,142,63,254,28,255,255,255,255,255,255,255,
		255,255,255,255,255,255,199,143,255,140,63,254,63,255,255,255,255,255,255,255,
		255,255,255,255,255,255,199,143,255,134,127,255,255,255,255,255,255,255,255,255,
		255,255,255,255,254,127,255,135,255,135,255,255,255,207,254,127,255,255,255,255,
		255,255,255,255,254,63,255,135,255,135,255,255,255,135,254,63,255,255,255,255,
		255,255,255,255,254,63,253,195,31,207,255,255,255,207,254,63,255,255,255,255,
		255,255,255,255,254,127,248,195,31,254,63,255,231,255,254,127,255,255,255,255,
		255,255,255,255,255,255,248,67,31,252,63,255,199,255,255,255,255,255,255,255,
		255,255,255,252,15,231,248,99,255,252,63,248,199,255,255,240,31,255,255,255,
		255,255,255,240,3,199,252,55,255,196,35,248,255,255,255,192,15,255,255,255,
		255,255,255,224,1,199,252,63,223,196,35,248,255,255,255,129,7,255,255,255,
		255,255,255,227,241,239,254,31,143,198,99,255,252,127,207,143,195,255,255,255,
		255,255,255,199,248,255,254,24,135,195,255,255,252,127,135,31,227,255,255,255,
		255,255,255,199,56,255,255,56,135,195,255,255,252,127,207,30,241,255,255,255,
		255,255,255,198,24,255,255,248,199,195,255,255,255,255,255,28,113,255,255,255,
		255,255,255,198,24,255,255,255,199,195,255,255,255,255,255,28,113,255,255,255,
		255,255,255,199,56,254,63,231,239,195,255,231,255,252,127,30,241,255,255,255,
		255,255,255,199,248,254,31,199,255,231,255,195,255,248,127,31,227,249,255,255,
		255,255,255,227,241,254,15,195,255,255,199,195,255,240,111,143,195,224,255,255,
		255,255,255,224,1,255,7,195,243,255,195,195,199,240,199,129,7,192,255,255,
		255,255,255,240,3,255,135,227,225,255,195,199,199,225,135,192,15,129,255,255,
		255,255,255,252,15,248,195,227,225,227,199,135,135,193,7,240,31,7,255,255,
		255,255,255,255,255,24,193,255,241,227,199,135,135,195,12,255,255,15,255,255,
		255,248,127,255,255,24,225,255,240,227,199,143,15,135,24,127,255,62,31,255,
		255,248,63,231,255,63,240,252,241,255,255,143,15,135,252,255,255,252,31,255,
		255,248,31,193,255,255,240,124,127,255,255,254,31,143,255,255,255,240,31,255,
		255,254,31,192,255,255,248,124,127,255,255,254,31,255,255,255,255,192,63,255,
		255,255,191,240,255,255,252,63,255,0,0,255,255,255,255,254,255,0,255,255,
		255,255,255,248,255,252,124,31,248,0,0,31,252,254,63,252,126,3,255,255,
		255,255,255,63,199,252,62,31,192,0,0,3,248,124,63,252,120,15,195,255,
		255,255,254,31,195,252,31,63,0,0,0,0,252,248,63,254,240,31,131,255,
		255,255,31,63,193,254,15,252,0,0,0,0,63,240,63,143,224,127,3,255,
		255,254,7,248,225,255,7,240,0,0,0,0,31,224,127,15,225,231,15,255,
		255,255,7,240,241,255,131,224,0,0,0,0,7,224,252,12,127,227,255,255,
		255,255,135,249,255,255,199,192,0,0,0,0,3,225,248,28,127,227,255,255,
		255,255,239,31,255,255,255,0,0,0,0,0,1,247,224,124,127,247,255,255,
		255,255,254,7,255,241,254,0,0,0,0,0,0,255,192,255,231,255,255,255,
		255,255,255,3,255,224,252,0,0,0,0,0,0,127,1,255,227,255,255,255,
		255,255,255,135,191,240,120,0,0,0,0,0,0,63,7,255,227,255,255,255,
		255,255,255,255,31,248,120,0,0,0,0,0,0,30,15,255,247,255,255,255,
		255,255,255,255,31,252,240,0,0,0,0,0,0,15,63,227,255,255,255,255,
		252,63,255,255,56,255,224,0,0,0,0,0,0,7,255,227,255,255,255,255,
		252,15,255,255,248,255,192,0,0,0,0,0,0,7,252,227,255,255,255,255,
		252,14,127,255,248,255,192,0,0,0,0,0,0,3,240,127,255,255,255,255,
		254,28,127,255,255,199,128,0,0,0,0,0,0,3,224,127,255,225,255,255,
		255,252,127,127,255,195,128,0,0,31,30,60,0,1,224,255,254,1,255,255,
		255,254,126,15,255,231,0,0,0,63,191,124,0,0,227,255,240,1,255,255,
		255,255,254,7,255,255,0,0,0,255,255,252,0,0,255,255,224,7,255,31,
		255,231,254,7,231,254,0,0,1,255,255,252,0,0,255,240,96,63,252,15,
		255,192,255,207,192,254,0,0,3,255,255,248,0,0,127,224,123,252,252,15,
		255,192,254,255,192,30,0,0,7,243,255,240,0,0,124,224,127,248,124,31,
		255,224,252,115,224,28,0,0,31,239,255,252,0,0,120,225,238,24,127,255,
		255,255,252,97,248,28,0,0,63,223,255,254,0,0,56,255,198,28,255,255,
		255,255,252,225,255,188,0,0,127,63,255,255,0,0,61,255,199,63,255,255,
		240,31,255,243,255,248,0,0,254,127,255,255,128,0,63,255,239,255,255,255,
		224,15,193,255,255,248,0,3,252,255,255,255,192,0,63,255,255,240,15,255,
		240,15,192,254,127,248,0,7,249,255,255,255,224,0,31,255,7,224,15,255,
		252,15,192,252,112,56,0,15,227,255,255,255,224,0,30,14,3,224,15,255,
		255,255,241,252,112,56,0,15,195,255,255,255,240,0,28,6,7,249,255,255,
		255,255,255,254,240,56,0,31,131,255,255,255,240,0,28,15,31,255,255,255,
		255,255,255,255,254,248,0,31,3,255,255,255,240,0,31,127,255,255,255,255,
		255,255,255,255,255,248,0,31,3,255,255,255,240,0,31,255,255,255,255,255,
		255,255,255,255,255,248,0,31,3,255,255,255,240,0,31,255,255,255,255,255,
		255,255,255,255,255,248,0,31,3,255,255,255,240,0,31,255,255,255,255,255,
		255,255,255,255,254,56,0,31,3,255,255,255,240,0,30,1,255,255,255,255,
		255,255,255,188,126,56,0,31,3,255,255,255,240,0,28,0,63,255,255,255,
		255,255,199,28,126,56,0,31,3,255,255,255,240,0,28,0,63,252,127,255,
		240,127,199,28,127,248,0,31,3,255,255,255,240,0,31,128,63,252,126,15,
		224,63,199,191,255,248,0,31,3,255,255,255,240,0,63,255,255,252,126,7,
		240,127,255,255,255,248,0,31,3,255,255,255,240,0,63,255,255,255,254,7,
		251,255,252,31,255,252,0,31,3,255,255,255,240,0,63,255,255,255,255,223,
		255,255,128,15,255,28,0,31,3,255,255,255,240,0,56,63,255,255,255,255,
		255,239,0,15,255,28,0,31,3,255,255,255,240,0,120,7,255,252,255,255,
		255,199,0,62,63,30,0,31,3,255,255,255,240,0,120,3,255,248,99,255,
		255,199,7,224,31,254,0,31,3,255,255,255,240,0,126,3,159,252,227,255,
		255,231,254,0,63,254,0,31,3,255,255,255,240,0,255,231,15,255,243,255,
		255,255,248,0,127,255,0,31,3,255,255,255,224,0,255,255,143,207,255,255,
		255,255,240,3,255,231,0,15,1,255,255,255,224,1,247,255,255,143,255,255,
		255,255,240,63,255,135,128,4,0,255,255,255,128,1,227,255,255,142,63,255,
		255,31,249,255,255,7,128,0,0,0,0,0,0,3,227,255,255,222,63,255,
		252,15,255,255,255,7,192,0,0,0,0,0,0,3,247,159,255,254,63,255,
		252,15,255,255,231,31,224,0,0,0,0,0,0,7,255,15,255,255,255,255,
		252,31,255,255,195,255,224,0,0,0,0,0,0,15,255,31,255,255,255,255,
		255,255,255,255,199,252,240,0,0,0,0,0,0,15,63,255,255,255,255,255,
		255,255,255,240,255,248,120,0,0,0,0,0,0,30,31,255,255,255,255,255,
		255,255,255,192,255,224,124,0,0,0,0,0,0,62,7,255,255,255,255,255,
		255,255,255,192,255,192,254,0,0,0,0,0,0,127,3,255,255,255,255,255,
		255,255,255,227,255,129,255,0,0,0,0,0,0,255,129,225,255,255,255,255,
		255,255,255,254,62,7,255,128,0,0,0,0,1,255,224,224,127,255,255,255,
		255,255,255,248,60,15,199,192,0,0,0,0,3,227,241,240,127,227,255,255,
		255,255,63,240,56,31,131,224,0,0,0,0,15,225,255,204,127,227,255,255,
		255,254,31,192,96,127,7,248,0,0,0,0,31,224,255,143,255,227,255,255,
		255,255,63,193,192,254,7,254,0,0,0,0,127,240,127,143,255,255,255,255,
		255,255,255,199,195,252,15,191,0,0,0,1,252,248,63,223,255,255,255,255,
		255,255,255,255,199,252,31,31,224,0,0,7,248,124,63,255,255,255,255,255,
		255,255,255,253,255,252,63,31,252,0,0,63,248,62,63,255,255,255,255,255,
		255,255,255,240,255,255,255,191,255,192,3,255,252,63,255,224,3,255,255,255,
		255,254,31,224,255,199,255,252,127,255,255,255,62,31,255,128,0,255,255,255,
		255,252,31,193,255,199,255,252,127,255,255,254,30,15,254,0,0,127,255,255,
		255,248,31,195,255,199,255,252,121,255,255,143,31,15,252,0,0,63,255,255,
		255,248,127,255,255,252,255,255,240,243,231,143,15,135,248,0,0,31,255,255,
		255,253,248,127,255,248,195,255,240,227,199,135,15,131,240,0,127,15,255,255,
		255,255,248,124,15,240,195,255,225,225,199,135,135,195,240,0,255,135,255,255,
		255,255,252,240,3,224,135,255,225,227,195,135,135,231,224,1,255,199,255,255,
		255,255,255,224,1,225,7,255,225,227,195,199,195,255,224,1,193,195,255,255,
		255,255,255,227,241,243,15,255,227,227,199,195,195,255,192,3,193,227,255,255,
		255,255,255,199,248,254,31,255,195,247,231,195,225,255,192,3,193,227,255,255,
		255,255,255,199,248,252,31,159,231,255,255,195,225,255,192,3,193,193,255,255,
		255,255,255,199,56,248,63,143,255,255,255,227,240,255,192,3,199,193,255,255,
		255,255,255,206,28,248,127,141,255,255,227,225,144,255,192,243,207,129,255,255,
		255,255,255,199,56,240,127,152,223,255,227,225,9,255,193,243,207,1,255,255,
		255,255,255,199,248,224,255,240,143,255,227,241,15,255,195,227,192,1,255,255,
		255,255,255,195,240,225,255,240,143,231,255,240,135,255,195,131,192,1,255,255,
		255,255,255,225,225,195,255,241,15,199,255,240,134,63,199,131,192,3,255,255,
		255,255,255,240,3,195,255,241,15,199,255,240,206,63,199,131,192,3,255,255,
		255,255,255,248,7,199,255,255,15,238,115,248,254,31,195,131,128,3,255,255,
		255,255,255,254,31,255,248,255,159,254,33,253,255,31,227,255,128,7,255,255,
		255,255,255,255,255,255,248,255,255,252,51,255,255,15,225,255,0,7,255,255,
		255,255,255,255,255,255,248,255,255,252,63,255,241,159,240,254,0,15,255,255,
		255,255,255,255,255,255,255,254,63,252,63,255,225,255,248,0,0,31,255,255,
		255,255,255,255,255,255,255,254,63,252,63,255,225,255,252,0,0,31,255,255,
		255,255,255,255,255,255,255,254,63,204,49,255,240,227,254,0,0,127,255,255,
		255,255,255,255,255,255,255,255,255,140,49,254,48,227,255,0,0,255,255,255,
		255,255,255,255,255,255,255,63,255,132,49,254,24,99,255,192,3,255,255,255,
		255,255,255,255,255,255,143,31,255,132,49,254,24,127,255,248,31,255,255,255,
		255,255,255,255,255,255,142,28,255,140,49,254,24,255,255,255,255,255,255,255,
		255,255,255,255,255,255,14,24,127,142,49,255,31,252,255,255,255,255,255,255,
		255,255,255,255,255,255,14,56,127,143,255,255,15,248,255,255,255,255,255,255,
		255,255,255,255,255,254,30,56,255,143,255,255,15,248,127,255,255,255,255,255,
		255,255,255,255,255,254,31,240,255,143,255,255,15,28,127,255,255,255,255,255,
		255,255,255,255,255,252,63,240,255,255,249,255,158,28,63,255,255,255,255,255,
		255,255,255,255,255,254,63,240,255,255,240,255,254,30,63,255,255,255,255,255,
		255,255,255,255,255,255,255,241,255,255,248,255,255,15,255,255,255,255,255,255,
		255,255,255,255,255,255,255,225,255,255,255,255,255,31,255,255,255,255,255,255,
		255,255,255,255,255,255,255,225,255,255,255,255,255,159,255,255,255,255,255,255,
		255,255,255,255,255,255,255,227,255,255,255,255,255,255,255,255,255,255,255,255,
		255,255,255,255,255,255,255,247,255,255,255,255,255,255,255,255,255,255,255,255,
		255,255,255,255,255,255,255,255,255,255,255,255,255,255,255,255,255,255,255,255,
		255,255,255,255,255,255,255,255,255,255,255,255,255,255,255,255,255,255,255,255,
		255,255,255,255,255,255,255,255,255,255,255,255,255,255,255,255,255,255,255,255,
		255,255,255,255,255,255,255,255,255,255,255,255,255,255,255,255,255,255,255,255,
		255,255,255,255,255,255,255,255,255,255,255,255,255,255,255,255,255,255,255,255

	]


	def set_user_and_password(self, username, password):
		self.username = username
		self.password = password

	def set_cafile(self, filename:str)->bool:
		if not os.path.exists(filename):
			print("cafile is not exists")
			exit(1)
		self.cafile = filename
		#print(self.lcd_logopic_160x20)
	
	def generate_random_str(self, randomlength=16):
		"""
		生成一个指定长度的随机字符串
		"""
		random_str = ''
		base_str = 'ABCDEFGHIGKLMNOPQRSTUVWXYZabcdefghigklmnopqrstuvwxyz0123456789'
		length = len(base_str) - 1
		for i in range(randomlength):
			random_str += base_str[random.randint(0, length)]
		return random_str

	def on_connect(self, mqttc, obj, flags, rc):
		#flags中的标志位能够知道此次连接时第一次连接还是短线后重连的
		try:
			print("Connection returned result: " + mqtt.connack_string(rc))
			if rc == 0:
				print("connect success")
			
			if self.publish_queue is not None:
				topic = "{}{}".format("/ctrl/", self.device_sn)
				self.publish_queue.put({"topic":topic, "payload":'hhh', 'qos':0, 'retain':False})
		except Exception as e:
			print("on_connect error:{}".format(e))

	#执行mqttc.disconnect()主动断开连接会触发该函数
	#当因为什么原因导致客户端断开连接时也会触发该函数,ctrl-c停止程序不会触发该函数
	def on_disconnect(self, mqttc, obj, rc):
		print("obj={}, rc={}".format(obj, rc))
		if obj is not None:
			mqttc.user_data_set(obj + 1)
			if obj == 0:
				mqttc.reconnect()

	'''
	mqttc:	the client instance for this callback
	obj:	the private user data as set in ``Client()`` or ``user_data_set()``
	msg:	an instance of MQTTMessage. This is a class with members ``topic``, ``payload``, ``qos``, ``retain``.
	'''
	def on_message(self, mqttc, obj, msg):
		msgjson = json.loads(str(msg.payload, encoding='utf-8'))
		if msgjson["sn"] == self.device_sn:
			print(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()) + ":on message:" + msg.topic + " " + str(msg.qos) + " " + str(msg.payload))

	def on_publish(self, mqttc, obj, mid):
		#重要，用来确认publish的消息发送出去了。有时即使publish返回成功，但消息却没有发送。
		#print("on public,mid:{}".format(mid))
		pass

	def on_subscribe(self, mqttc, obj, mid, granted_qos):
		print("Subscribed: " + str(mid) + " " + str(granted_qos))
	
	def setsubscribe(self, topic=None, qos=0):
		self.sub_topic_list.append((topic, qos))

	def set_deviceid(self, devid):
		self.device_sn = devid

	def do_select(self):
		self.publish_queue = queue.Queue(8)
		while True:
			try:
				if not self.publish_queue.empty():
					msg = self.publish_queue.get()
					#print("{}:i publish: {}".format(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()), msg))
					bytemsg = bytes(self.lcd_logopic_160x20)
					bHead = bytes("ZYWL", encoding='utf-8')
					bCmd = 12
					bIdentify = 0xbbdd
					bBodyHead0 = 0xaa
					bBodyHead1 = 0x55
					bBodyType = 0xfa
					bImageLenght = 3200
					fmt = "<4sBHIBBBH3200s"
					bytemsg = struct.pack(fmt, bHead, bCmd, bIdentify, int(time.time()), bBodyHead0, bBodyHead1, bBodyType, bImageLenght, bytes(self.lcd_logopic_160x20))
					print("bytemsg={}".format(str(bytemsg)))
					print("bytemsg type={} len={}".format(type(bytemsg), len(bytemsg)))
					info = self.publish(topic = msg["topic"], payload = bytemsg, qos = msg["qos"], retain = msg["retain"])
					if info.rc == mqtt.MQTT_ERR_SUCCESS:
						#self.delete_list.append({"mid":info.mid, "msg":msg})
						info.wait_for_publish()
				time.sleep(0.1)
			except Exception as e:
				print("select error:{}".format(e))  

	def start_publish_thread(self):    
		publish_thread = threading.Thread(target = self.do_select)
		publish_thread.setDaemon(True)
		publish_thread.start()

	def run(self, host=None, port=1883, keepalive=60):
		self.reconnect_delay_set(min_delay=10, max_delay=120)

		self.username_pw_set(self.username, self.password)
		self.tls_set(ca_certs=self.cafile, certfile=None, keyfile=None, cert_reqs=ssl.CERT_REQUIRED, tls_version=ssl.PROTOCOL_TLSv1_1)
		self.tls_insecure_set(False)
		
		self.connect(host, port, keepalive)
		self.subscribe(self.sub_topic_list)
		self.loop_forever()

if __name__ == "__main__":
	'''
	client_id:	唯一用户id,不能和其他客户端有相同的。如果设置为None,则自动生成一个随机id,设置为None是clean_session必须为True
   	clean_session:	设置为True时，当客户端断开broker会删除所有关于该客户端的信息.如果为False,客户端断开期间的消息会被保留。
					客户端断开时不会丢弃自己发送出的消息，调用connect或reconnect将导致消息重新发送。
	userdata=None	
	protocol=MQTTv311 or MQTTv31
	transport="tcp" or "websockets"
	'''

	if len(sys.argv) < 1:
		print("run like this:")
		print("python3 script.py [device sn]")
		exit(1)

	devid = sys.argv[1]

	host = "mqtt.iotwonderful.cn"
	port = 8883
	user = "test_001"
	passwd = "NjBlNjY3ZWRlZ"
	cafile = "./.mqtt.iotwonderful.cn.crt"
	crtfile= ''' 
-----BEGIN CERTIFICATE-----
MIIEATCCAumgAwIBAgIJAJueN6AjXSA0MA0GCSqGSIb3DQEBCwUAMIGWMQswCQYD
VQQGEwJDTjEQMA4GA1UECAwHQmVpamluZzEQMA4GA1UEBwwHQmVpamluZzEVMBMG
A1UECgwMSW90V29uZGVyZnVsMQwwCgYDVQQLDANQcmQxFTATBgNVBAMMDGlvdHdv
bmRlcmZ1bDEnMCUGCSqGSIb3DQEJARYYd3VzaHVhaUBpb3R3b25kZXJmdWwuY29t
MB4XDTIwMDYwOTA3MDcwNVoXDTMwMDYwNzA3MDcwNVowgZYxCzAJBgNVBAYTAkNO
MRAwDgYDVQQIDAdCZWlqaW5nMRAwDgYDVQQHDAdCZWlqaW5nMRUwEwYDVQQKDAxJ
b3RXb25kZXJmdWwxDDAKBgNVBAsMA1ByZDEVMBMGA1UEAwwMaW90d29uZGVyZnVs
MScwJQYJKoZIhvcNAQkBFhh3dXNodWFpQGlvdHdvbmRlcmZ1bC5jb20wggEiMA0G
CSqGSIb3DQEBAQUAA4IBDwAwggEKAoIBAQC4Wjj7eziKCl1bESQUumO0Er00a9YW
vMC4zR3v63esqbthjN5mqP0zd30Z5uVyn0dzum0a1Un7WlIdsaEQUW5HcixfmUDc
sBVep0XmmWxtuVzMUpPVRVWUtIbagL8RJjx2cpb33w2t2lDxh5Gj7phZTPDDlyI6
OSSjauUlv1mOpkHcDBi0iU/wqUXUEo7hsBUft/6uMQK27HXlGn8TvgRT1oXFEVZo
HvPf9sDRjDxV39iNEhUKRHX2dxxsgLbA6IqI1W2k0h+WVnafp7hjy9QCbjRkBGWK
1HJ/HqICNBv+UTURsn7DFDioEcuFELGFf0m9Z5nVT7O7Pek10Q7BVBivAgMBAAGj
UDBOMB0GA1UdDgQWBBS7sWlXl0ZdB5LXA9/TCmk9mdVwRzAfBgNVHSMEGDAWgBS7
sWlXl0ZdB5LXA9/TCmk9mdVwRzAMBgNVHRMEBTADAQH/MA0GCSqGSIb3DQEBCwUA
A4IBAQBKw3odroL+BPLewpskJ228+PqqvSQvC3MwMfRA9r6rvIGqQmlW8Utj0Gux
x7MiDo9wgj61DnndbrSac/oJ5icT8gI7suKeCSh23eLQ58MxZuJzYCekT2s4qVAi
VLbeb7b4iQadlt3TeIjzvvj60qEHq4Md0SOf1gc01tGc6fMW7Ql29P4RdD682Xad
KaSWcB3N/NRGZ0zW9321tUgN6VKOEOWqt4vt9G2mPViLeUH7ZVB1gor+pR4N6ljG
C0FvxTyyS61Jgy/zDfPidUOGCUGukl67T5xQjlewckKnyrTORLDIvMgvLdyD3y2U
tXfw8qEIFXkmqPXch2AyF5Jq6iTE
-----END CERTIFICATE-----
	'''

	if not os.path.exists(cafile):
		with open(cafile, "w") as w:
			w.write(crtfile)

	print("host={}, port={}, username={}, password={}, cafile={}".format(host, port, user, passwd, cafile))
	mc = mqtt_client(	client_id = "id_shenyang_test_qrreq_type3",
						clean_session = False,
						userdata = None,
						protocol = mqtt.MQTTv31,
						transport = 'tcp')
	mc.setsubscribe(topic="/response", qos=0)
	mc.set_user_and_password(user, passwd)
	mc.set_cafile(cafile)
	mc.set_deviceid(devid)
	mc.start_publish_thread()
	mc.run(host=host, port=port, keepalive=60)

