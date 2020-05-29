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

class mqtt_client(mqtt.Client):

	debug = True
	username = None
	password = None
	verbose = False
	sub_topic_list = []

	publish_queue = None
	delete_list = []
	logger = None
	
	def on_connect(self, mqttc, obj, flags, rc):
		#flags中的标志位能够知道此次连接时第一次连接还是短线后重连的
		print(flags)
		print("rc={}".format(rc))
		print("Connection returned result: " + mqtt.connack_string(rc))
		if rc == 0:
			print("connect success")

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
		print("on message:" + msg.topic + " " + str(msg.qos) + " " + str(msg.payload))
		if msg.retain == 0:
			print("retain = Flase")
			if self.publish_queue is not None:
				self.publish_queue.put({"topic":'/public/TEST/duan/will', "payload":b'get hello world', 'qos':1, 'retain':True})
		else:
			if obj == True:
				print("Clearing topic " + msg.topic)
			print("retain = True")

	def on_publish(self, mqttc, obj, mid):
		#重要，用来确认publish的消息发送出去了。有时即使publish返回成功，但消息却没有发送。
		print("on public,mid:{}".format(mid))
		for item in self.delete_list:
			if mid == item["mid"]:
				print("on publish remove msg, mid={}".format(mid))
				self.delete_list.remove(item)

	def on_subscribe(self, mqttc, obj, mid, granted_qos):
		print("Subscribed: " + str(mid) + " " + str(granted_qos))

	def on_log(self, mqttc, obj, level, string):
		print(string)

	def setsubscribe(self, topic=None, qos=0):
		self.sub_topic_list.append((topic, qos))

	def do_select(self):
		self.publish_queue = queue.Queue(8)
		while True:
			try:
				if not self.publish_queue.empty():
					msg = self.publish_queue.get()
					info = self.publish(topic = msg["topic"], payload = msg["payload"], qos = msg["qos"], retain = msg["retain"])
					if info.rc == mqtt.MQTT_ERR_SUCCESS:
						self.delete_list.append({"mid":info.mid, "msg":msg})
						info.wait_for_publish()
				time.sleep(0.1)
				for wait in self.delete_list:
					msg = wait["msg"]
					print("resend mesage from delete list")
					info = self.publish(topic = msg["topic"], payload = msg["payload"], qos = msg["qos"], retain = msg["retain"])
					if info.rc == mqtt.MQTT_ERR_SUCCESS:
						print("resend success, remove {}".format(wait))
						self.delete_list.remove(wait)
			except Exception as e:
				print("select error:{}".format(e))	
			
	def run(self, host=None, port=1883, keepalive=60):
		thread_select = threading.Thread(target = self.do_select)
		thread_select.setDaemon(False)
		thread_select.start()

		self.will_set(topic='/public/TEST/duan/will', payload="test will message!", qos=2, retain=False)
		self.reconnect_delay_set(min_delay=10, max_delay=120)
		logging.basicConfig(level=logging.INFO)
		self.logger = logging.getLogger(__name__)
		#self.enable_logger(self.logger)
		'''
		if not usetls:
			tlsVersion = None
		else:
			tlsVersion = ssl.PROTOCOL_TLSv1_2
			#tlsVersion = ssl.PROTOCOL_TLSv1_1
			#tlsVersion = ssl.PROTOCOL_TLSv1

		if secure:
			cert_required = ssl.CERT_REQUIRED
		else:
			cert_required = ssl.CERT_NONE

		#mqttc.tls_set(ca_certs=None, certfile=None, keyfile=None, cert_reqs=cert_required, tls_version=tlsVersion)	
		#mqttc.tls_insecure_set(True)
		'''
		
		self.username_pw_set(self.username, self.password)
		self.connect(host, port, keepalive)
		#self.subscribe(topic)
		'''
		for topic, qos in self.sub_topic_list:
			print("topic:{} qos:{}".format(topic, qos))
			self.subscribe(topic, qos)
		'''
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
	mc = mqtt_client(	client_id = "client_id_duan12", 
						clean_session = False,
						userdata = None,
						protocol = mqtt.MQTTv31,
						transport = 'tcp')
	mc.setsubscribe(topic='/public/TEST/duan', qos=0)
	mc.setsubscribe(topic='/public/TEST/duan/qos1', qos=1)
	mc.setsubscribe(topic='/public/TEST/duan/qos2', qos=2)
	mc.run(host="mq.tongxinmao.com", port=18830, keepalive=60)
