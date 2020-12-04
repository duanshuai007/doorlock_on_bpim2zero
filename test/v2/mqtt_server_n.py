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
from logger import LoggingProducer, LoggingConsumer
import config

class mqtt_client(mqtt.Client):
	username = None
	password = None
	logger = None
	sub_topic_list = []
	online_device_list = []
	
	ASK_TOPIC = "/acs/ask"
	RESPONSE_TOPIC = "/acs/response"
	CTRL_TOPIC = "/acs/ctrl/"

	cmd_num2str_list = [
		None,
		"ask",
		"ctrldoor",
		None,
		"download qrcode",
		None,
		"group ctrl",
		"set doorlock time",
		None,
		None,
		None,
		"set system time",
		None,
		"set doorlock level"
	]

	cmd_resp_num2str_dict = {
		"device online" : 100,
		"device offline" : 101,
		"opendoor ok" : 102,
		"opendoor fail" : 103,
		"download qr ok" : 106,
		"download qr fail" : 107,
		"set group ok" : 110,
		"set group fail" : 111,
		"set door opentime ok" : 112,
		"set door opentime fail" : 113,
		"set door openlevel ok" : 124,
		"set door openlevel fail" : 125,
	} 

	def set_logger(self, logger):
		self.logger = logger

	def set_user_and_password(self, username, password):
		self.username = username
		self.password = password

	def set_cafile(self, filename:str)->bool:
		if not os.path.exists(filename):
			self.logger.info("cafile is not exists")
			exit(1)
		self.cafile = filename

	def on_connect(self, mqttc, obj, flags, rc):
		#flags中的标志位能够知道此次连接时第一次连接还是短线后重连的
		self.logger.info("onConnection returned result: " + mqtt.connack_string(rc))
		if rc == 0:
			self.logger.info("connect success")

	#执行mqttc.disconnect()主动断开连接会触发该函数
	#当因为什么原因导致客户端断开连接时也会触发该函数,ctrl-c停止程序不会触发该函数
	def on_disconnect(self, mqttc, obj, rc):
		self.logger.info("onDisconnect obj={}, rc={}".format(obj, rc))
		if obj is not None:
			mqttc.user_data_set(obj + 1)
			if obj == 0:
				mqttc.reconnect()

	def print_logger(self, topic:str, jsonmsg:dict, msgtype:int):
		try:
			if msgtype == 0:
				if "message" in jsonmsg.keys():
					self.logger.info("===>topic[{}]:cmd={}({}), time={}, identify={}, message={}".format(topic, jsonmsg["cmd"], self.cmd_num2str_list[jsonmsg["cmd"]], jsonmsg["time"], jsonmsg["identify"], jsonmsg["message"]))
				else:
					self.logger.info("===>topic[{}]:cmd={}({}), time={}, identify={}".format(topic, jsonmsg["cmd"], self.cmd_num2str_list[jsonmsg["cmd"]], jsonmsg["time"], jsonmsg["identify"]))
			else:
				respstr = None
				for key in self.cmd_resp_num2str_dict.keys():
					if self.cmd_resp_num2str_dict[key] == jsonmsg["resp"]:
						respstr = key
						break
				self.logger.info("<===topic[{}]:sn={}, resp={}({}), time={}, identify={}".format(topic, jsonmsg["sn"], jsonmsg["resp"], respstr, jsonmsg["time"], jsonmsg["identify"]))
		except Exception as e:
			self.logger.error("print_logger error:{}".format(e))
	'''
	mqttc:	the client instance for this callback
	obj:	the private user data as set in ``Client()`` or ``user_data_set()``
	msg:	an instance of MQTTMessage. This is a class with members ``topic``, ``payload``, ``qos``, ``retain``.
	'''
	def on_message(self, mqttc, obj, msg):
		try:
			#self.logger.info(":on message:" + msg.topic + " " + str(msg.qos) + " " + str(msg.payload))
			msgstr = str(msg.payload, encoding='utf-8')
			msgjson = json.loads(msgstr)
			if msg.topic == self.ASK_TOPIC:
				self.print_logger(msg.topic, msgjson, 0)
			elif msg.topic == self.RESPONSE_TOPIC:
				'''
				get device response
				{
					"sn" : "",
					"time" : 0,
					"identify" : 0,
					"resp" : 0,
				}
				'''
				resp = msgjson["resp"]
				if resp == 200 or resp == 100:
					self.logger.info("topic[{}]=>dev[{}]:online ".format(self.RESPONSE_TOPIC, msgjson["sn"]))
				elif resp == 201:
					self.logger.info("topic[{}]=>dev[{}]:offline".format(self.RESPONSE_TOPIC, msgjson["sn"]))
				else:
					if  resp % 2 == 0:
						cmd = int(( resp + 2 - 100 ) / 2)
					else:
						cmd = int(( resp + 1 - 100 ) / 2)
					self.print_logger(msg.topic, msgjson, 1)
			elif msg.topic.startswith(self.CTRL_TOPIC):
				self.print_logger(msg.topic, msgjson, 0)
				pass
		except Exception as e:
			self.logger.info("on message exception:{}".format(e))

	def on_publish(self, mqttc, obj, mid):
		#重要，用来确认publish的消息发送出去了。有时即使publish返回成功，但消息却没有发送。
		pass

	def on_subscribe(self, mqttc, obj, mid, granted_qos):
		self.logger.info("onSubscribed: " + str(mid) + " " + str(granted_qos))
	
	def setsubscribe(self, topic=None, qos=0):
		self.sub_topic_list.append((topic, qos))
	
	def work_threading(self):
		try:
			while True:
				time.sleep(1)
				cur = int(time.time())
				for item in self.online_device_list:
					if len(item) == 0:
						continue
					if cur - item["time"] >= 300 or item["onesend"] == True:	#300 Seconds = 5 Minutes
						item["time"] = cur
						item["onesend"] = False
						topic = "{}{}".format("/ctrl/", item["sn"])
						ctrlmsg = {
							"cmd" : 5,
							"identify" : random.randint(0, 65535),
							"time" : int(time.time()),
							"message" : {
								"data" : "this is a test string,and have a random number in there=>{}".format(random.randint(100000, 999999)),
							}
						}
#						sendmsg = json.dumps(ctrlmsg)
#self.logger.info("send ctrl message to {}".format(item["sn"]))
#						self.publish(topic = topic, payload = sendmsg, qos=0, retain = False)
		except Exception as e:
			self.logger.error("work_threading error:{}".format(e))


	def run(self, host=None, port=1883, keepalive=60):
		self.reconnect_delay_set(min_delay=10, max_delay=120)

		t = threading.Thread(target = self.work_threading, args=[])
		t.setDaemon(True)
		t.start()

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


	host = config.MQTT_SERVER_URL
	port = config.MQTT_SERVER_PORT
	user = config.MQTT_USER
	passwd = config.MQTT_PASSWD
	cafile = config.MQTT_CAFILE_PATH

	LoggingConsumer()
	logger = LoggingProducer().getlogger()

	if not os.path.exists(cafile):
		with open(cafile, "w") as w:
			w.write(crtfile)
	
	logger.info("host={}, port={}, username={}, password={}, cafile={}".format(host, port, user, passwd, cafile))
	mc = mqtt_client(	client_id = "iot_acs_doorlock_monitor", 
						clean_session = False,
						userdata = None,
						protocol = mqtt.MQTTv31,
						transport = 'tcp')
	mc.setsubscribe(topic="#", qos=0)
	mc.set_logger(logger)
	mc.set_user_and_password(user, passwd)
	mc.set_cafile(cafile)
	mc.run(host=host, port=port, keepalive=60)

