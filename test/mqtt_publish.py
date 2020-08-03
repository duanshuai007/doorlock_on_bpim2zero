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
import config
import json
import message_struct as ms

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

	def do_select(self):
		self.publish_queue = queue.Queue(8)
		while True:
			try:
				if not self.publish_queue.empty():
					#print("get publish message")
					msg = self.publish_queue.get()
					print("{}:i publish: {}".format(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()), msg))
					info = self.publish(topic = msg["topic"], payload = msg["payload"], qos = msg["qos"], retain = msg["retain"])
					if info.rc == mqtt.MQTT_ERR_SUCCESS:
						#self.delete_list.append({"mid":info.mid, "msg":msg})
						info.wait_for_publish()
				time.sleep(0.1)
				'''
				for wait in self.delete_list:
					msg = wait["msg"]
					#print("resend mesage from delete list")
					info = self.publish(topic = msg["topic"], payload = msg["payload"], qos = msg["qos"], retain = msg["retain"])
					if info.rc == mqtt.MQTT_ERR_SUCCESS:
						print("resend success, remove {}".format(wait))
						self.delete_list.remove(wait)
				'''
			except Exception as e:
				print("select error:{}".format(e))	
	

	def test_publish(self):
		#devid = "0a2c1867f161"
		#devid = "d66fabdd3dce"
		#devid = "02420877c9cc"
#devid = "02421a71c57b"
		#devid = "024251720577"
		devid = "0242fe007c52"
		#devid = "ffffffffffff"
		message_delay = 10
		ms.OPENDOOR_MSG["device_sn"] = devid
		ms.OPENDOOR_MSG["action"] = 1
		ms.OPENDOOR_MSG["identify"] = 123456678765432
		
		ms.QR_GETWX2VCODE["device_sn"] = devid
		ms.QR_GETWX2VCODE["type"] = 1
		ms.QR_GETWX2VCODE["identify"] = 32198321892319
		ms.QR_GETWX2VCODE["message"]["page"] = ""
		ms.QR_GETWX2VCODE["message"]["scene"] = "h=2"

		ms.QR_DOWN2VCODE["device_sn"] = devid
		ms.QR_DOWN2VCODE["type"] = 2
		ms.QR_DOWN2VCODE["identify"] = 3321321321986
		ms.QR_DOWN2VCODE["message"]["download"] = "https://timgsa.baidu.com/timg?image&quality=80&size=b9999_10000&sec=1591866200525&di=e880ae3dc16c07985a292a24f3842a1d&imgtype=0&src=http%3A%2F%2Ft9.baidu.com%2Fit%2Fu%3D770196171%2C1212335633%26fm%3D193"

		ms.QR_GENERATE2VCODE["device_sn"] = devid
		ms.QR_GENERATE2VCODE["type"] = 3
		ms.QR_GENERATE2VCODE["identify"] = 39389043910329
		ms.QR_GENERATE2VCODE["message"]["data"] = "this is a test message, this will create a 2vcode and display on 160x160 matrix screen"
		
		ms.DEVICE_INFO["device_sn"] = "ffffffffffff"

		ms.UPDATE_INFO["device_sn"] = devid
		ms.UPDATE_INFO["firmware"]["url"] = "http://wwww.baidu.com"
		ms.UPDATE_INFO["firmware"]["version"] = 4
		ms.UPDATE_INFO["firmware"]["packetsize"] = 1024
		ms.UPDATE_INFO["firmware"]["enable"] = 1
		ms.UPDATE_INFO["firmware"]["md5"] = 3829183210838201

		ms.OPENSSH_INFO["device_sn"] = devid
	
		while True:
			#time.sleep(3)
			#print("test_publish")
			if self.publish_queue is not None:
				#print("test puiblish send message")
				#self.publish_queue.put({"topic":"/acs_open", "payload":"{\"device_sn\":\"00001\"},\"action\":1,\"identify\":\"1234567\"", 'qos':2, 'retain':False})
				'''	
				ms.OPENDOOR_MSG["action"] = 0
				ms.OPENDOOR_MSG["stime"] = int(time.time())
				sendmsg = json.dumps(ms.OPENDOOR_MSG)
				self.publish_queue.put({"topic":ms.OPENDOOR_TOPIC, "payload":sendmsg, 'qos':1, 'retain':False})
				time.sleep(10)
				'''
				'''	
				ms.OPENDOOR_MSG["action"] = 1
				ms.OPENDOOR_MSG["stime"] = int(time.time())
				sendmsg = json.dumps(ms.OPENDOOR_MSG)
				self.publish_queue.put({"topic":ms.OPENDOOR_TOPIC, "payload":sendmsg, 'qos':1, 'retain':False})
				time.sleep(message_delay)
				
				ms.QR_GETWX2VCODE["stime"] = int(time.time())
				sendmsg = json.dumps(ms.QR_GETWX2VCODE)
				self.publish_queue.put({"topic":ms.QR_TOPIC, "payload":sendmsg, 'qos':1, 'retain':False})
				time.sleep(message_delay)

				ms.QR_DOWN2VCODE["stime"] = int(time.time())
				sendmsg = json.dumps(ms.QR_DOWN2VCODE)
				self.publish_queue.put({"topic":ms.QR_TOPIC, "payload":sendmsg, 'qos':1, 'retain':False})
				time.sleep(message_delay)

				ms.QR_GENERATE2VCODE["stime"] = int(time.time())
				sendmsg = json.dumps(ms.QR_GENERATE2VCODE)
				self.publish_queue.put({"topic":ms.QR_TOPIC, "payload":sendmsg, 'qos':1, 'retain':False})
				time.sleep(message_delay)
				'''	
	
				
				ms.DEVICE_INFO["device_sn"] = "ffffffffffff"			
				ms.DEVICE_INFO["stime"] = int(time.time())
				ms.DEVICE_INFO["doorlock"] = 20
				sendmsg = json.dumps(ms.DEVICE_INFO)
				self.publish_queue.put({"topic":ms.DEVICE_INFO_TOPIC, "payload":sendmsg, 'qos':1, 'retain':False})
				time.sleep(5)
				

				'''
				ms.UPDATE_INFO["stime"] = int(time.time())
				sendmsg = json.dumps(ms.UPDATE_INFO)
				self.publish_queue.put({"topic":ms.UPDATE_TOPIC, "payload":sendmsg, 'qos':2, 'retain':False})
				time.sleep(10)
				'''

				'''
				ms.OPENSSH_INFO["stime"] = int(time.time())
				ms.OPENSSH_INFO["enable"] = 0
				ms.OPENSSH_INFO["opentime"] = 300
				sendmsg = json.dumps(ms.OPENSSH_INFO)
				self.publish_queue.put({"topic":ms.OPENSSH_TOPIC, "payload":sendmsg, 'qos':0, 'retain':False})
				time.sleep(20)
				'''

				'''
				ms.OPENSSH_INFO["stime"] = int(time.time())
				ms.OPENSSH_INFO["enable"] = 0
				ms.OPENSSH_INFO["opentime"] = 300
				sendmsg = json.dumps(ms.OPENSSH_INFO)
				self.publish_queue.put({"topic":ms.OPENSSH_TOPIC, "payload":sendmsg, 'qos':0, 'retain':False})
				time.sleep(20)
				'''

				time.sleep(0.01)
				pass
				
				
	def start_publish_thread(self):		
		publish_thread = threading.Thread(target = self.do_select)
		publish_thread.setDaemon(False)
		publish_thread.start()
		test_pub = threading.Thread(target = self.test_publish)
		test_pub.setDaemon(False)
		test_pub.start()
			
	def run(self, host=None, port=1883, keepalive=60):
		#self.will_set(topic=ms.DEVICE_ONLINE_TOPIC, payload=respjson, qos=2, retain=False)
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
	publish_flag = False
	if sys.argv[1] == "p":
		publish_flag = True
	elif sys.argv[1] == "s":
		publish_flag = False
	elif sys.argv[1] == "ps":
		publish_flag = True

	c = config.config("/home/swann/workgit/acs/test/config.ini")
	host = c.get("MQTT", "HOST")
	port = int(c.get("MQTT", "PORT"))
	user = c.get("MQTT", "USER")
	passwd = c.get("MQTT", "PASSWD")
	cafile = c.get("MQTT", "CAFILE")

	print("host={}, port={}, username={}, password={}, cafile={}".format(host, port, user, passwd, cafile))
	mc = mqtt_client(	client_id = "id_shenyang_test_all_subscribe111", 
						clean_session = False,
						userdata = None,
						protocol = mqtt.MQTTv31,
						transport = 'tcp')
	mc.setsubscribe(topic='/acs_open', qos=1)
	mc.setsubscribe(topic='/qr_code', qos=1)
	mc.setsubscribe(topic=ms.OPENDOOR_RESP_TOPIC, qos=2)
	mc.setsubscribe(topic=ms.QR_RESP_TOPIC, qos=2)
	mc.setsubscribe(topic=ms.DEVICE_STATUS_TOPIC, qos=2)
	mc.setsubscribe(topic=ms.DEVICE_INFO_RESP_TOPIC, qos=0)
	mc.setsubscribe(topic=ms.UPDATE_RESP_TOPIC, qos=2)
	mc.setsubscribe(topic=ms.OPENSSH_RESP_TOPIC, qos=0)
	with open("./device_sn.table", "r") as f:
		while True:
			linemsg = f.readline().split('\n')[0]
			if len(linemsg) == 0:
				break
			print(linemsg)
			device_status_topic = "{}/{}".format(ms.DEVICE_STATUS_TOPIC, linemsg)
			mc.setsubscribe(topic=device_status_topic, qos=0)
		

	mc.set_user_and_password(user, passwd)
	mc.set_cafile(cafile)
	if publish_flag == True:
		mc.start_publish_thread()
	mc.run(host=host, port=port, keepalive=60)

