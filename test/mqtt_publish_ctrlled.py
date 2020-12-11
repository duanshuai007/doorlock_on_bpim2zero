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
import config

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
		print("Connection returned result: " + mqtt.connack_string(rc))
		if rc == 0:
			print("connect success")
		opendoor = {
			"device_sn" : self.devid,
			"action" : self.ledstatus,
			"identify" : 123456678765432,
			"stime" : int(time.time())
		}
		if self.publish_queue is not None:
			sendmsg = json.dumps(opendoor)
			self.publish_queue.put({"topic":"/door_ctrl", "payload":sendmsg, 'qos':0, 'retain':False})

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
		print(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()) + ":on message:" + msg.topic + " " + str(msg.qos) + " " + str(msg.payload))
		try:
			if msg.retain == 0:
				#print("retain = Flase")
				pass
			else:
				if obj == True:
					print("Clearing topic " + msg.topic)
				#print("retain = True")
		except Exception as e:
			print("on message exception:{}".format(e))

	def on_publish(self, mqttc, obj, mid):
		#重要，用来确认publish的消息发送出去了。有时即使publish返回成功，但消息却没有发送。
		#print("on public,mid:{}".format(mid))
		'''
		for item in self.delete_list:
			if mid == item["mid"]:
				#print("on publish remove msg, mid={}".format(mid))
				self.delete_list.remove(item)
		'''
		pass

	def on_subscribe(self, mqttc, obj, mid, granted_qos):
		print("Subscribed: " + str(mid) + " " + str(granted_qos))
	'''
	def on_log(self, mqttc, obj, level, string):
		print(string)
	'''
	def setsubscribe(self, topic=None, qos=0):
		self.sub_topic_list.append((topic, qos))

	def set_deviceid_and_ledstatus(self, devid, ledstatus):
		self.devid = devid
		self.ledstatus = ledstatus

	def do_select(self):
		self.publish_queue = queue.Queue(8)
		while True:
			try:
				if not self.publish_queue.empty():
					msg = self.publish_queue.get()
					print("{}:i publish: {}".format(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()), msg))
					info = self.publish(topic = msg["topic"], payload = msg["payload"], qos = msg["qos"], retain = msg["retain"])
					if info.rc == mqtt.MQTT_ERR_SUCCESS:
						#self.delete_list.append({"mid":info.mid, "msg":msg})
						info.wait_for_publish()
						break
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
	if len(sys.argv) < 2:
		print("run like this:")
		print("python3 script.py deviceid ledenable[1/0]")
		exit(1)

	devid = sys.argv[1]
	ledstatus = sys.argv[2]
	
	host = config.MQTT_SERVER_HOST
	port = config.MQTT_SERVER_PORT
	user = config.MQTT_USERNAME
	passwd = config.MQTT_PASSWORD
	cafile = config.MQTT_CAFILE

	if not os.path.exists(cafile):
		with open(cafile, "w") as w:
			w.write(crtfile)

	print("host={}, port={}, username={}, password={}, cafile={}".format(host, port, user, passwd, cafile))
	mc = mqtt_client(
						clean_session = True,
						userdata = None,
						protocol = mqtt.MQTTv311,
						transport = 'tcp')
	mc.setsubscribe(topic="/door_response", qos=2)
	mc.set_user_and_password(user, passwd)
	mc.set_cafile(cafile)
	mc.set_deviceid_and_ledstatus(devid, ledstatus)
	mc.start_publish_thread()
	mc.run(host=host, port=port, keepalive=60)

