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
import copy
import random

import display.generate_pillow_buffer as sc
from LoggingQueue import LoggingProducer, LoggingConsumer
import display.wx2vcode as wx
import message_struct as ms
import spilcd_api

class mqtt_client(mqtt.Client):
	#debug = True
	logger = None
	
	sub_topic_list = []
	delete_list = []

	wx2vcode = None

	def set_device_sn(self, sn):
		self.device_sn = sn	

	def set_wx2vcode_hand(self, hand, screen):
		self.wx2vcode = hand
		self.screen = screen
		#self.screen.closesceen()

	def set_logger(self, logger):
		self.logger = logger

	def set_user_and_password(self, username, password):
		self.username_pw_set(username, password)

	def set_cafile(self, filename:str)->bool:
		try:
			if not os.path.exists(filename):
				self.logger.error("cafile is not exists")
				exit(1)
			self.tls_set(ca_certs=filename, certfile=None, keyfile=None, cert_reqs=ssl.CERT_REQUIRED, tls_version=ssl.PROTOCOL_TLSv1_1)
			self.tls_insecure_set(False)
			return True
		except Exception as e:
			self.logger.error("tls_set error:{}".format(e))
			return False

	def on_connect(self, mqttc, obj, flags, rc):
		#flags中的标志位能够知道此次连接时第一次连接还是短线后重连的
		self.logger.info("Connection returned result: " + mqtt.connack_string(rc))
		if rc == 0:
			self.logger.info("connect success")
			self.subscribe(self.sub_topic_list)
			
			resp = copy.deepcopy(ms.DEVICE_ONLINE)
			resp["device_sn"] = self.device_sn
			resp["rtime"] = int(time.time())
			resp["on_line"] = 1
			resp["identify"] = random.randint(100000, 999999)
			respjson = json.dumps(resp)
			self.publish_queue.put({"topic":ms.DEVICE_ONLINE_TOPIC, "payload":respjson, 'qos':2, 'retain':False})

	#执行mqttc.disconnect()主动断开连接会触发该函数
	#当因为什么原因导致客户端断开连接时也会触发该函数,ctrl-c停止程序不会触发该函数
	def on_disconnect(self, mqttc, obj, rc):
		self.logger.info("on_disconnect obj={}, rc={}".format(obj, rc))
		#if obj is not None:
			#mqttc.user_data_set(obj + 1)
			#if obj == 0:
		mqttc.reconnect()

	'''
	mqttc:	the client instance for this callback
	obj:	the private user data as set in ``Client()`` or ``user_data_set()``
	msg:	an instance of MQTTMessage. This is a class with members ``topic``, ``payload``, ``qos``, ``retain``.
	'''
	def on_message(self, mqttc, obj, msg):
		try:
			if msg.retain == 0:
				#self.logger.info("retain = Flase")
				json_msg = json.loads(str(msg.payload, encoding="utf-8"))
				if json_msg["device_sn"] == self.device_sn:
					self.logger.info("on message:" + msg.topic + " " + str(msg.qos) + " " + str(msg.payload))
					local_time = int(time.time())
					recv_time = int(json_msg["stime"])
					if (local_time - recv_time < 10):
						if self.work_queue is not None:
							self.work_queue.put([msg.topic, json_msg])
						else:
							#device busy，message lost
							pass
					else:
						#timeout, message lost
						self.logger.warn("on message: this message timestamp was timeout")
						if msg.topic == ms.OPENDOOR_TOPIC:
							ms.OPENDOOR_RESP_MSG["device_sn"] = self.device_sn
							ms.OPENDOOR_RESP_MSG["result"] = 2
							ms.OPENDOOR_RESP_MSG["identify"] = json_msg["identify"]
							ms.OPENDOOR_RESP_MSG["rtime"] = int(time.time())
							sendmsg = json.dumps(ms.OPENDOOR_RESP_MSG)
							self.publish_queue.put({"topic":ms.OPENDOOR_RESP_TOPIC, "payload":sendmsg, 'qos':2, 'retain':False})
						else:
							ms.QR_RESPONSE["device_sn"] = self.device_sn
							ms.QR_RESPONSE["rtime"] = int(time.time())
							ms.QR_RESPONSE["type"] = json_msg["type"]
							ms.QR_RESPONSE["identify"] = json_msg["identify"]
							ms.QR_RESPONSE["status"] = 2
							sendmsg = json.dumps(ms.OPENDOOR_RESP_MSG)
							self.publish_queue.put({"topic":ms.QR_RESP_TOPIC, "payload":sendmsg, 'qos':2, 'retain':False})
			else:
				#if obj == True:
				#	self.logger.info("Clearing topic " + msg.topic)
				self.logger.info("retain = True:{} {} {}".format(msg,topic, msg,qos, msg.payload))
		except Exception as e:
			self.logger.error("on message exception:{}".format(e))

	def on_publish(self, mqttc, obj, mid):
		#重要，用来确认publish的消息发送出去了。有时即使publish返回成功，但消息却没有发送。
		for item in self.delete_list:
			if mid == item["mid"]:
				self.logger.info("on publish remove msg, mid={}".format(mid))
				self.delete_list.remove(item)
		pass

	def on_subscribe(self, mqttc, obj, mid, granted_qos):
		self.logger.info("Subscribed: " + str(mid) + " " + str(granted_qos))

	'''
	def on_log(self, mqttc, obj, level, string):
		self.logger.info(string)
	'''

	def setsubscribe(self, topic=None, qos=0):
		self.sub_topic_list.append((topic, qos))

	def do_select(self):
		self.publish_queue = queue.Queue(32)
		while True:
			try:
				if not self.publish_queue.empty():
					msg = self.publish_queue.get()
					info = self.publish(topic = msg["topic"], payload = msg["payload"], qos = msg["qos"], retain = msg["retain"])
					if info.rc == mqtt.MQTT_ERR_SUCCESS:
						#self.delete_list.append({"mid":info.mid, "msg":msg})
						info.wait_for_publish()
				time.sleep(0.01)
				'''
				for wait in self.delete_list:
					msg = wait["msg"]
					self.logger.info("resend mesage from delete list")
					info = self.publish(topic = msg["topic"], payload = msg["payload"], qos = msg["qos"], retain = msg["retain"])
					if info.rc == mqtt.MQTT_ERR_SUCCESS:
						self.logger.info("resend success, remove {}".format(wait))
						self.delete_list.remove(wait)
				'''
			except Exception as e:
				self.logger.info("select error:{}".format(e))	
	
	def do_hardware_work(self):
		self.work_queue = queue.Queue(32)
		doorlock_open_flag = False
		doorlock_open_time = 0
		doorlock_continue_time = int(config.config().get("DOORLOCK", "OPEN_TIME")) * 1000
		image_show_flag = False
		image_show_time = 0
		image_continue_time = int(config.config().get("DOORLOCK", "2VCODE_TIME")) * 1000
		spilcd_api.on()
		while True:
			try:
				if not self.work_queue.empty():
					[topic, json_msg] = self.work_queue.get()
					#json_msg = json.loads(str(msg.payload, encoding="utf-8"))
					#self.logger.info("topic={}, msg={}".format(topic, json_msg))
					if topic == ms.OPENDOOR_TOPIC:
						#执行开锁动作,返回动作响应信息
						if json_msg["action"] == 1:
							gpio_val = 0
							doorlock_open_flag = True
							doorlock_open_time = int(time.time() * 1000)
						else:
							gpio_val = 1
						
						spilcd_api.set_doorlock(gpio_val)
						ms.OPENDOOR_RESP_MSG["device_sn"]	= self.device_sn
						ms.OPENDOOR_RESP_MSG["rtime"]		= int(time.time())
						ms.OPENDOOR_RESP_MSG["result"]		= 1
						ms.OPENDOOR_RESP_MSG["identify"]	= json_msg["identify"]
						sendmsg = json.dumps(ms.OPENDOOR_RESP_MSG)
						self.publish_queue.put({"topic":ms.OPENDOOR_RESP_TOPIC, "payload":sendmsg, 'qos':2, 'retain':False})
						pass
					elif topic == ms.QR_TOPIC:
						#执行显示二维码动作,该动作不需要返回响应信息
						ms.QR_RESPONSE["device_sn"] = self.device_sn
						ms.QR_RESPONSE["rtime"]		= int(time.time())
						ms.QR_RESPONSE["type"]		= json_msg["type"]
						ms.QR_RESPONSE["identify"]  = json_msg["identify"]
						ms.QR_RESPONSE["status"]	= 0
						if json_msg["type"] == 1:
							filepath = self.wx2vcode.get_2vcode(json_msg["message"])
							if filepath is not None:
								ret = self.screen.show_image_on_screen(filepath, True, True)
								if ret == True:
									ms.QR_RESPONSE["status"] = 1
									image_show_flag = True
									image_show_time = int(time.time() * 1000)
						elif json_msg["type"] == 3:
							ret = self.screen.show_qrcode_2vcode_on_screen(json_msg["message"])
							if ret == True:
								ms.QR_RESPONSE["status"] = 1
								image_show_flag = True
								image_show_time = int(time.time() * 1000)
						elif json_msg["type"] == 2:
							ret = self.screen.down_image_and_show_image_on_screen(json_msg["message"])
							if ret == True:
								ms.QR_RESPONSE["status"] = 1
								image_show_flag = True
								image_show_time = int(time.time() * 1000)
						else:
							pass

						if ms.QR_RESPONSE["status"] == 0:
							self.screen.show_erroricon()

						sendmsg = json.dumps(ms.QR_RESPONSE)
						self.publish_queue.put({"topic":ms.QR_RESP_TOPIC, "payload":sendmsg, 'qos':2, 'retain':False})
					else:
						self.logger.info("invaild topic = {}".format(topic))
						#send response failed
				'''
				if doorlock_open_flag == True:
					curtime = int(time.time() * 1000)
					#self.logger.info("curtime={} opentime={}".format(curtime, doorlock_open_time))
					if curtime - doorlock_open_time > doorlock_continue_time:	#1000ms
						#self.gpio_handler.writePin(self.gpio_group, self.gpio_pin, 1)
						spilcd_api.set_doorlock(1)
						doorlock_open_flag = False
				if image_show_flag == True:
					curtime = int(time.time() * 1000)
					if curtime - image_show_time > image_continue_time:
						#clear screen
						#spilcd_api.close_screen()
						self.screen.show_logo()
						image_show_flag = False
						pass
				'''
				time.sleep(0.01)
			except Exception as e:
				self.logger.info("do hardware work except:{}".format(e))

	def start_other_thread(self):
		publish_thread = threading.Thread(target = self.do_select)
		publish_thread.setDaemon(False)
		publish_thread.start()
		
		work_thread = threading.Thread(target = self.do_hardware_work)
		work_thread.setDaemon(False)
		work_thread.start()

	def run_mqtt(self, host=None, port=1883, keepalive=60):
		try:
			resp = copy.deepcopy(ms.DEVICE_ONLINE)
			resp["device_sn"] = self.device_sn
			resp["rtime"] = int(time.time())
			resp["on_line"] = 0 
			resp["identify"] = random.randint(100000, 999999)
			respjson = json.dumps(resp)
			self.will_set(topic=ms.DEVICE_ONLINE_TOPIC, payload=respjson, qos=2, retain=False)
			self.reconnect_delay_set(min_delay=10, max_delay=60)
			#logging.basicConfig(level=logging.INFO)
			#self.logger = logging.getLogger(__name__)
			self.connect(host, port, keepalive)
			'''
			for topic, qos in self.sub_topic_list:
				self.logger.info("topic:{} qos:{}".format(topic, qos))
				self.subscribe(topic, qos)
			'''
			return True
		except Exception as e:
			self.logger.error("run error:{}".format(e))
			return False


if __name__ == "__main__":
	'''
	client_id:	唯一用户id,不能和其他客户端有相同的。如果设置为None,则自动生成一个随机id,设置为None是clean_session必须为True
   	clean_session:	设置为True时，当客户端断开broker会删除所有关于该客户端的信息.如果为False,客户端断开期间的消息会被保留。
					客户端断开时不会丢弃自己发送出的消息，调用connect或reconnect将导致消息重新发送。
	userdata=None	
	protocol=MQTTv311 or MQTTv31
	transport="tcp" or "websockets"
	'''
	if len(sys.argv) < 2:
		print("paramter must be 2")
		exit(1)
	device_sn = sys.argv[1]

	LoggingConsumer()
	logger = LoggingProducer().getlogger()

	c = config.config()
	host = c.get("MQTT", "HOST")
	port = int(c.get("MQTT", "PORT"))
	user = c.get("MQTT", "USER")
	passwd = c.get("MQTT", "PASSWD")
	cafile = c.get("MQTT", "CAFILE")
	wx2vcode_hand = wx.wx_2vcode()
	logger.info("host={}, port={}, username={}, password={}, cafile={}".format(host, port, user, passwd, cafile))
	mc = mqtt_client(	client_id = device_sn, 
						clean_session = True,
						userdata = None,
						protocol = mqtt.MQTTv31,
						transport = 'tcp')
	mc.set_logger(logger)
	mc.set_device_sn(device_sn)
	mc.setsubscribe(topic=ms.OPENDOOR_TOPIC, qos=0)
	mc.setsubscribe(topic=ms.QR_TOPIC, qos=0)
	mc.set_user_and_password(user, passwd)
	if mc.set_cafile(cafile) == False:
		exit(1)
	time.sleep(0.2)
	screen = sc.screen()
	mc.set_wx2vcode_hand(wx2vcode_hand, screen)
	if mc.run_mqtt(host=host, port=port, keepalive=60) == False:
		exit(1)
	mc.start_other_thread()
	mc.loop_forever()
