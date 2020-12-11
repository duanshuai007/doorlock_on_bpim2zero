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
import config

class mqtt_client(mqtt.Client):
	username = None
	password = None
	
	def set_user_and_password(self, username, password):
		self.username = username
		self.password = password

	def set_cafile(self, filename:str)->bool:
		if not os.path.exists(filename):
			print("cafile is not exists")
			exit(1)
		self.cafile = filename

	def set_deviceid(self, devid, url):
		self.device_sn = devid
		self.downloadurl = url

	def run(self, host=None, port=1883, keepalive=60):
		self.reconnect_delay_set(min_delay=10, max_delay=120)

		self.username_pw_set(self.username, self.password)
		self.tls_set(ca_certs=self.cafile, certfile=None, keyfile=None, cert_reqs=ssl.CERT_REQUIRED, tls_version=ssl.PROTOCOL_TLSv1_1)
		self.tls_insecure_set(False)
		
		self.connect(host, port, keepalive)

		qr_generate2vcode = {
			"cmd" : 4,	#设备自己生成二维码
			"identify" : random.randint(0, 65535),
			"time" : int(time.time()),
			"message" : {
				"url" : self.downloadurl,
			},
		}
		sendmsg = json.dumps(qr_generate2vcode)
		topic = "{}{}".format("/acs/ctrl/", self.device_sn)
		self.publish(topic = topic, payload = sendmsg, qos = 0, retain = False)

if __name__ == "__main__":
	'''
	client_id:	唯一用户id,不能和其他客户端有相同的。如果设置为None,则自动生成一个随机id,设置为None是clean_session必须为True
   	clean_session:	设置为True时，当客户端断开broker会删除所有关于该客户端的信息.如果为False,客户端断开期间的消息会被保留。
					客户端断开时不会丢弃自己发送出的消息，调用connect或reconnect将导致消息重新发送。
	userdata=None	
	protocol=MQTTv311 or MQTTv31
	transport="tcp" or "websockets"
	'''

	if len(sys.argv) < 3:
		print("run like this:")
		print("python3 script.py [device sn] [download url]")
		exit(1)

	devid = sys.argv[1]
	dlurl = sys.argv[2]

	host = config.MQTT_SERVER_URL
	port = config.MQTT_SERVER_PORT
	user = config.MQTT_USER
	passwd = config.MQTT_PASSWD
	cafile = config.MQTT_CAFILE_PATH
	print("host={}, port={}, username={}, password={}, cafile={}".format(host, port, user, passwd, cafile))
	mc = mqtt_client(	
						clean_session = True,
						userdata = None,
						protocol = mqtt.MQTTv311,
						transport = 'tcp')
	mc.set_user_and_password(user, passwd)
	mc.set_cafile(cafile)
	mc.set_deviceid(devid, dlurl)
	mc.run(host=host, port=port, keepalive=60)

