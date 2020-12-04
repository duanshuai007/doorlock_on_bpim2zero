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

	#debug = True
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

	#执行mqttc.disconnect()主动断开连接会触发该函数
	#当因为什么原因导致客户端断开连接时也会触发该函数,ctrl-c停止程序不会触发该函数
	def set_groupid(self, gid, gmsg):
		self.gid = gid
		self.gmsg = gmsg

	def run(self, host=None, port=1883, keepalive=60):
		self.reconnect_delay_set(min_delay=10, max_delay=120)

		self.username_pw_set(self.username, self.password)
		self.tls_set(ca_certs=self.cafile, certfile=None, keyfile=None, cert_reqs=ssl.CERT_REQUIRED, tls_version=ssl.PROTOCOL_TLSv1_1)
		self.tls_insecure_set(False)
		
		self.connect(host, port, keepalive)
		qr_generate2vcode = {
			"cmd" : 1,	#设备自己生成二维码
			"identify" : random.randint(0, 65535),
			"time" : int(time.time()),
			"message" : {
				"data" : self.gmsg,
			},
		}

		sendmsg = json.dumps(qr_generate2vcode)
		topic = "{}{}".format("/acs/ctrl/", self.gid)
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
		print("python3 script.py [group id] [group message]")
		exit(1)

	gid = int(sys.argv[1])
	gmsg = sys.argv[2]

	host = config.MQTT_SERVER_URL
	port = config.MQTT_SERVER_PORT
	user = config.MQTT_USER
	passwd = config.MQTT_PASSWD
	cafile = config.MQTT_CAFILE_PATH

	if not os.path.exists(cafile):
		with open(cafile, "w") as f:
			f.write(config.MQTT_CAFILE_MESSAGE)

	print("host={}, port={}, username={}, password={}, cafile={}".format(host, port, user, passwd, cafile))
	mc = mqtt_client(	client_id = "id_shenyang_test_qrreq_type3",
						clean_session = False,
						userdata = None,
						protocol = mqtt.MQTTv31,
						transport = 'tcp')
	mc.set_user_and_password(user, passwd)
	mc.set_cafile(cafile)
	mc.set_groupid(gid, gmsg)
	mc.run(host=host, port=port, keepalive=60)

