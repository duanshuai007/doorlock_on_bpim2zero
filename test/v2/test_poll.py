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
	delete_list = []
	send_msg_list = []
	connect_flag = False

	def set_user_and_password(self, username, password):
		self.username = username
		self.password = password

	def set_cafile(self, filename:str)->bool:
		if not os.path.exists(filename):
			print("cafile is not exists")
			exit(1)
		self.cafile = filename

	def on_connect(self, mqttc, obj, flags, rc):
		#flags中的标志位能够知道此次连接时第一次连接还是短线后重连的
		try:
			print("Connection returned result: " + mqtt.connack_string(rc))
			self.connect_flag = True
			if rc == 0:
				print("connect success")
		except Exception as e:
			print("on_connect error:{}".format(e))

	#执行mqttc.disconnect()主动断开连接会触发该函数
	#当因为什么原因导致客户端断开连接时也会触发该函数,ctrl-c停止程序不会触发该函数
	def on_disconnect(self, mqttc, obj, rc):
		print("obj={}, rc={}".format(obj, rc))
		self.connect_flag = False
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
		msgjson = json.loads(str(msg.payload, encoding="utf-8"))
		if msgjson["sn"] == self.device_sn:
			print(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()) + ":on message:" + msg.topic + " " + str(msg.qos) + " " + str(msg.payload))
			for item in self.send_msg_list:
				if item["id"] == msgjson["identify"]:
					self.send_msg_list.remove(item)

	def on_publish(self, mqttc, obj, mid):
		#重要，用来确认publish的消息发送出去了。有时即使publish返回成功，但消息却没有发送。
		pass

	def on_subscribe(self, mqttc, obj, mid, granted_qos):
		print("Subscribed: " + str(mid) + " " + str(granted_qos))

	def set_deviceid(self, devid):
		self.device_sn = devid

	def do_select(self):
		self.publish_queue = queue.Queue(8)
		i = 0
		while True:
			try:
				if self.connect_flag == True:
					jmsg = {
						"cmd" : 4,
						"identify" : i,
						"time" : int(time.time()),
						"message" : {
							"url" : 
						}
					}
					sjmsg = json.dumps(jmsg)
					topic = "{}{}".format("/acs/ctrl/", self.device_sn)
					print("{}:i publish: {}".format(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()), sjmsg))
					info = self.publish(topic = topic, payload = sjmsg, qos = 0, retain = 0)
					if info.rc == mqtt.MQTT_ERR_SUCCESS:
						info.wait_for_publish()
					self.send_msg_list.append({"id":i})
					time.sleep(30)
					i = i + 1
				else:
					time.sleep(0.1)
			except Exception as e:
				print("select error:{}".format(e))  


	def do_check(self):
		timer=0
		local_error_count = 0
		while True:
			try:
				time.sleep(1)
				timer = timer + 1
				if timer >= 10:
					timer = 0
					if (len(self.send_msg_list) != local_error_count):
						print("faile msg = {}".format(len(self.send_msg_list)))
						local_error_count = len(self.send_msg_list)
			except Exception as e:
				print("check error:{}".format(e))

	def start_publish_thread(self):    
		publish_thread = threading.Thread(target = self.do_select)
		publish_thread.setDaemon(True)
		publish_thread.start()
		check_thread = threading.Thread(target = self.do_check)
		check_thread.setDaemon(True)
		check_thread.start()

	def run(self, host=None, port=1883, keepalive=60):
		self.reconnect_delay_set(min_delay=10, max_delay=120)
		self.username_pw_set(self.username, self.password)
		self.tls_set(ca_certs=self.cafile, certfile=None, keyfile=None, cert_reqs=ssl.CERT_REQUIRED, tls_version=ssl.PROTOCOL_TLSv1_1)
		self.tls_insecure_set(False)
		
		self.connect(host, port, keepalive)
		self.loop_forever()

if __name__ == "__main__":
	if len(sys.argv) < 2:
		print("run like this:")
		print("python3 script.py deviceid ledenable[1/0]")
		exit(1)

	devid = sys.argv[1]

	host = config.MQTT_SERVER_URL
	port = config.MQTT_SERVER_PORT
	user = config.MQTT_USER
	passwd = config.MQTT_PASSWD
	cafile = config.MQTT_CAFILE_PATH

	if not os.path.exists(cafile):
		with open(cafile, "w") as f:
			f.write(config.MQTT_CAFILE_MESSAGE)

	print("host={}, port={}, username={}, password={}, cafile={}".format(host, port, user, passwd, cafile))
	mc = mqtt_client(	
						clean_session = True,
						userdata = None,
						protocol = mqtt.MQTTv311,
						transport = 'tcp')
	mc.set_user_and_password(user, passwd)
	mc.set_cafile(cafile)
	mc.set_deviceid(devid)
	mc.start_publish_thread()
	time.sleep(0.5)
	mc.run(host=host, port=port, keepalive=60)

