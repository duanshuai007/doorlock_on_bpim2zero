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
import copy
import random
import signal

import config
import generate_pillow_buffer as sc
from LoggingQueue import LoggingProducer, LoggingConsumer
import wx2vcode as wx
import message_struct as ms
import spilcd_api
import downloadfile as downloadtool

class mqtt_client(mqtt.Client):
	#debug = True
	logger = None
	
	sub_topic_list = []
	delete_list = []

	wx2vcode = None
	publish_queue = None
	work_queue = None
	status = None
	exit_flag = False
	update_flag = False
	
	update_status_file = "/home/ubuntu/update_status"
	update_end_file = "/home/ubuntu/update_end"

	def set_device_sn(self, sn):
		self.device_sn = sn	
		self.status_topic = "{}/{}".format(ms.DEVICE_STATUS_TOPIC, sn)
		self.work_queue = queue.Queue(32)
		self.publish_queue = queue.Queue(32)
		self.wx2vcode = wx.wx_2vcode()
		self.screen = sc.screen()

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
			if self.exit_flag == False or self.update_flag == False:
				self.logger.info("connect success")
				self.subscribe(self.sub_topic_list)
				
				self.status = "success"
				ms.DEVICE_STATUS["status"] = 1
				ms.DEVICE_STATUS["rtime"] = int(time.time())
				respjson = json.dumps(ms.DEVICE_STATUS)
				self.publish_queue.put({"topic":self.status_topic, "payload":respjson, 'qos':0, 'retain':True})

				if os.path.exists(self.update_status_file):
					with open(self.update_status_file, 'r') as f:
						try:
							line = f.read(32).split('\n')[0]
							result = line.split(':')[0]
							version = line.split(':')[1]
							reason = line.split(':')[2]
							ms.UPDATE_RESP_INFO["device_sn"] = self.device_sn
							ms.UPDATE_RESP_INFO["rtime"] = int(time.time())
							ms.UPDATE_RESP_INFO["firmware"]["version"] = version
							if result == "success":
								#send firmware update success message
								ms.UPDATE_RESP_INFO["firmware"]["status"] = "success"
							else:
								ms.UPDATE_RESP_INFO["firmware"]["status"] = "{}:{}".format(result, reason)
							sendmsg = json.dumps(ms.UPDATE_RESP_INFO)
							self.publish_queue.put({"topic":ms.UPDATE_RESP_TOPIC, "payload":sendmsg, 'qos':2, 'retain':False})
						except Exception as e:
							self.logger.error("read update status file error:{}".format(e))
					os.remove(self.update_status_file)
				if os.path.exists(self.update_end_file):
					os.remove(self.update_end_file)

	#执行mqttc.disconnect()主动断开连接会触发该函数
	#当因为什么原因导致客户端断开连接时也会触发该函数,ctrl-c停止程序不会触发该函数
	def on_disconnect(self, mqttc, obj, rc):
		self.status = "failed"	
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
			if self.exit_flag == False or self.update_flag == False:
				json_msg = json.loads(str(msg.payload, encoding="utf-8"))
				if json_msg["device_sn"] == self.device_sn or json_msg["device_sn"] == ms.BOARDCAST_ADDR:
					self.logger.info("on message:" + msg.topic + " " + str(msg.qos) + " " + str(msg.payload))
					local_time = int(time.time())
					recv_time = int(json_msg["stime"])
					if msg.topic == ms.UPDATE_TOPIC:
						self.work_queue.put([msg.topic, json_msg])
					else:
						if (abs(local_time - recv_time) < 15):
							if self.work_queue is not None:
								self.work_queue.put([msg.topic, json_msg])
							else:
								#device busy，message lost
								self.logger.error("on message:self.work_queue is None")
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
								self.publish_queue.put({"topic":ms.OPENDOOR_RESP_TOPIC, "payload":sendmsg, 'qos':0, 'retain':False})
							elif msg.topic == ms.QR_TOPIC:
								ms.QR_RESPONSE["device_sn"] = self.device_sn
								ms.QR_RESPONSE["rtime"] = int(time.time())
								ms.QR_RESPONSE["type"] = json_msg["type"]
								ms.QR_RESPONSE["identify"] = json_msg["identify"]
								ms.QR_RESPONSE["status"] = 2
								sendmsg = json.dumps(ms.OPENDOOR_RESP_MSG)
								self.publish_queue.put({"topic":ms.QR_RESP_TOPIC, "payload":sendmsg, 'qos':0, 'retain':False})
							else:
								#topic format: recvtopic + "_resp"
								resp_topic = "{}_resp".format(msg.topic)
								resp_dict = {
									"device_sn" : self.device_sn,
									"rtime" : int(time.time()),
									"status" : 1,
									"error" : "timeout",
								}
								respmsg = json.dumps(resp_dict)
								self.publish_queue.put({"topic":resp_topic, "payload":respmsg, 'qos':0, 'retain':False})
								pass
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

	def do_hardware_work(self):
		MQTT_CONNECT_SUCCESS_SIG = int(config.config("/root/config.ini").get("SIGNAL", "MQTTCONNOK"))
		MQTT_CONNECT_FAILED_SIG = int(config.config("/root/config.ini").get("SIGNAL", "MQTTCONNBAD"))
		doorlock_open_flag = False
		doorlock_open_time = 0
		doorlock_time = int(config.config("/root/config.ini").get("DOORLOCK", "OPEN_TIME"))
		doorlock_continue_time = doorlock_time * 1000
		image_show_flag = False
		image_show_time = 0
		image_continue_time = int(config.config("/root/config.ini").get("DOORLOCK", "2VCODE_TIME")) * 1000
		spilcd_api.on()
		while True:
			try:
				if not self.publish_queue.empty():
					msg = self.publish_queue.get()
					info = self.publish(topic = msg["topic"], payload = msg["payload"], qos = msg["qos"], retain = msg["retain"])
					if info.rc == mqtt.MQTT_ERR_SUCCESS:
						#self.delete_list.append({"mid":info.mid, "msg":msg})
						info.wait_for_publish()
				if self.status is not None:
					pid = int(os.popen("ps -ef | grep zywlstart | grep -v grep | awk -F\" \" '{print $2}'").read().split('\n')[0])
					if self.status == "success":
						os.kill(pid, MQTT_CONNECT_SUCCESS_SIG)
					else:
						os.kill(pid, MQTT_CONNECT_FAILED_SIG)
					#connect_status="{}".format(self.status)
					#with open("/root/mqtt_connect_status", "w") as f:
					#	f.write(connect_status)
					self.status = None
				if not self.work_queue.empty():
					[topic, json_msg] = self.work_queue.get()
					#json_msg = json.loads(str(msg.payload, encoding="utf-8"))
					#self.logger.info("topic={}, msg={}".format(topic, json_msg))
					if topic == ms.OPENDOOR_TOPIC:
						#执行开锁动作,返回动作响应信息
						if json_msg["action"] == 1 or json_msg["action"] == "1":
							#高电平门锁断电，能够打开
							gpio_val = 1
							doorlock_open_flag = True
							doorlock_open_time = int(time.time() * 1000)
						else:
							#低电平门锁给电，不能打开
							gpio_val = 0
						
						spilcd_api.set_doorlock(gpio_val)
						ms.OPENDOOR_RESP_MSG["device_sn"]	= self.device_sn
						ms.OPENDOOR_RESP_MSG["rtime"]		= int(time.time())
						ms.OPENDOOR_RESP_MSG["result"]		= 1
						ms.OPENDOOR_RESP_MSG["identify"]	= json_msg["identify"]
						sendmsg = json.dumps(ms.OPENDOOR_RESP_MSG)
						self.publish_queue.put({"topic":ms.OPENDOOR_RESP_TOPIC, "payload":sendmsg, 'qos':0, 'retain':False})
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
							#self.logger.info("wx2ccode ret = {}".format(filepath))
							if filepath is not None:
								#self.logger.info("filepath = {}".format(filepath))
								ret = self.screen.show_image_on_screen(filepath, True, True)
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
						elif json_msg["type"] == 3:
							ret = self.screen.show_qrcode_2vcode_on_screen(json_msg["message"])
							if ret == True:
								ms.QR_RESPONSE["status"] = 1
								image_show_flag = True
								image_show_time = int(time.time() * 1000)
						else:
							pass
						
						if ms.QR_RESPONSE["status"] == 0:
							self.screen.show_erroricon()
						
						sendmsg = json.dumps(ms.QR_RESPONSE)
						self.publish_queue.put({"topic":ms.QR_RESP_TOPIC, "payload":sendmsg, 'qos':0, 'retain':False})
					else:
						if topic == ms.UPDATE_TOPIC:
							self.update_flag = True
							version = int(config.config("/root/config.ini").get("FIRMWARE", "VERSION"))
							update_version = int(json_msg["firmware"]["version"])
							ms.UPDATE_RESP_INFO["device_sn"] = self.device_sn
							ms.UPDATE_RESP_INFO["firmware"]["version"] = update_version
							ms.UPDATE_RESP_INFO["rtime"] = int(time.time())
							if version >= update_version:
								#当前版本高于等待升级的版本，不升级
								ms.UPDATE_RESP_INFO["firmware"]["status"] = "ignore"
								sendmsg = json.dumps(ms.UPDATE_RESP_INFO)
								self.publish_queue.put({"topic":ms.UPDATE_RESP_TOPIC, "payload":sendmsg, 'qos':0, 'retain':False})
								pass
							else:
								#当前版本低于等待升级的版本，进行升级
								if os.path.exists(self.update_status_file):
									ms.UPDATE_RESP_INFO["firmware"]["status"] = "updating"
									sendmsg = json.dumps(ms.UPDATE_RESP_INFO)
									self.publish_queue.put({"topic":ms.UPDATE_RESP_TOPIC, "payload":sendmsg, 'qos':0, 'retain':False})
								else:
									ms.UPDATE_RESP_INFO["firmware"]["status"] = "ready"
									sendmsg = json.dumps(ms.UPDATE_RESP_INFO)
									self.publish_queue.put({"topic":ms.UPDATE_RESP_TOPIC, "payload":sendmsg, 'qos':0, 'retain':False})
									packetsize = json_msg["firmware"]["packetsize"]
									md5str = json_msg["firmware"]["md5"]
									download_url = json_msg["firmware"]["url"]
									filename = "/home/download/firmware_{}.des3.tar.gz".format(json_msg["firmware"]["version"])
									if downloadtool.download_firmware(download_url, md5str, filename) == True:
										ms.UPDATE_RESP_INFO["firmware"]["status"] = "download success"
										ms.UPDATE_RESP_INFO["rtime"] = int(time.time())
										sendmsg = json.dumps(ms.UPDATE_RESP_INFO)
										self.publish_queue.put({"topic":ms.UPDATE_RESP_TOPIC, "payload":sendmsg, 'qos':0, 'retain':False})
										self.exit_flag = True
										time.sleep(0.5)
										with open(self.update_status_file, "w") as f:
											update_message="{}:{}:0".format("start", update_version)
											f.write(update_message)
									else:
										ms.UPDATE_RESP_INFO["firmware"]["status"] = "download failed"
										ms.UPDATE_RESP_INFO["rtime"] = int(time.time())
										sendmsg = json.dumps(ms.UPDATE_RESP_INFO)
										self.publish_queue.put({"topic":ms.UPDATE_RESP_TOPIC, "payload":sendmsg, 'qos':0, 'retain':False})
										self.update_flag = False
									
						elif topic == ms.OPENSSH_TOPIC:
							enable = json_msg["enable"]
							opentime = json_msg["opentime"]
							ms.OPENSSH_RESP_INFO["device_sn"] = self.device_sn
							if enable == 0:	#close ssh
								cmd = "service frpc stop"
								ret = "close"
								os.system(cmd)
								pass
							else:	#open ssh
								cmd = "service frpc start"
								ret = "open"
								os.system(cmd)
								pass
							ms.OPENSSH_RESP_INFO["status"] = ret
							ms.OPENSSH_RESP_INFO["rtime"] = int(time.time())
							sendmsg = json.dumps(ms.OPENSSH_RESP_INFO)
							self.publish_queue.put({"topic":ms.OPENSSH_RESP_TOPIC, "payload":sendmsg, 'qos':0, 'retain':False})
							pass
						elif topic == ms.DEVICE_INFO_TOPIC:
							ms.DEVICE_INFO["device_sn"] = self.device_sn
							#doorlock  = 0: get doorlock time
							#doorlock != 0: set doorlock time
							if json_msg["doorlock"] != 0:
								c = config.config("/root/config.ini")
								ret = c.set("DOORLOCK", "OPEN_TIME", str(json_msg["doorlock"]))
								if ret == False:
									ms.DEVICE_INFO["doorlock"] = "failed"
								else:
									doorlock_time = int(json_msg["doorlock"])
									doorlock_continue_time = doorlock_time * 1000
									ms.DEVICE_INFO["doorlock"] = "success"
								pass
							else:
								ms.DEVICE_INFO["doorlock"] = doorlock_time
									
							current = os.popen("cat /tmp/current_network").read().split('\n')[0]
							ms.DEVICE_INFO["current"] = current
							
							cmd1="ifconfig {} | grep 'inet addr' ".format(current)
							cmd2 = "{}{}{}{}".format(" | awk -F\" \" ", "'{", "print $2", "}'")
							cmd3 = "{}{}{}{}".format(" | awk -F\":\" ", "'{", "print $2", "}'")
							cmd = "{}{}{}".format(cmd1, cmd2, cmd3)
							ip = os.popen(cmd).read().split('\n')[0]
							ms.DEVICE_INFO["ip"] = ip
							sendmsg = json.dumps(ms.DEVICE_INFO)
							self.publish_queue.put({"topic":ms.DEVICE_INFO_RESP_TOPIC, "payload":sendmsg, 'qos':0, 'retain':False})
							pass
						elif topic == ms.WLAN_CONFIG_TOPIC:
							ssid = json_msg["wlan"]["ssid"]
							psk = json_msg["wlan"]["psk"]
							ms.WLAN_CONFIG_RESP_INFO["device_sn"] = self.device_sn
							ms.WLAN_CONFIG_RESP_INFO["rtime"] = int(time.time())
							ms.WLAN_CONFIG_RESP_INFO["status"] = 0

							shellcmd = "/root/set_current_wifi.sh wlan {} {}".format(ssid, psk)
							self.logger.info("set wlan:cmd={}".format(shellcmd))
							os.system(shellcmd)
							retssid = os.popen("cat /root/net.conf | grep ssid | awk -F\"=\" '{print $2}'").read().split('\n')[0]
							retpsk = os.popen("cat /root/net.conf | grep psk | awk -F\"=\" '{print $2}'").read().split('\n')[0]
							if retssid == ssid and retpsk == psk:
								ms.WLAN_CONFIG_RESP_INFO["status"] = 1
							sendmsg = json.dumps(ms.WLAN_CONFIG_RESP_INFO)
							self.publish_queue.put({"topic":ms.WLAN_CONFIG_RESP_TOPIC, "payload":sendmsg, 'qos':0, 'retain':False})
						else:
							self.logger.info("invaild topic = {}".format(topic))
							#send response failed
				
				if doorlock_open_flag == True:
					curtime = int(time.time() * 1000)
					if curtime - doorlock_open_time > doorlock_continue_time:	#1000ms
						spilcd_api.set_doorlock(0)
						doorlock_open_flag = False
				'''
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
		self.exit_flag = False
		self.exit_signal = int(config.config("/root/config.ini").get("SIGNAL", "EXITFLAG"))
		signal.signal(self.exit_signal, self.exit_handler)
		work_thread = threading.Thread(target = self.do_hardware_work)
		work_thread.setDaemon(False)
		work_thread.start()

	def exit_handler(self):
		self.exit_flag = True

	def run_mqtt(self, host=None, port=1883, keepalive=60):
		try:
			ms.DEVICE_STATUS["status"] = 0
			ms.DEVICE_STATUS["rtime"] = int(time.time())
			respjson = json.dumps(ms.DEVICE_STATUS)
			self.will_set(topic=self.status_topic, payload=respjson, qos=0, retain=True)
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


def client_start():
	''' 
	client_id:  唯一用户id,不能和其他客户端有相同的。如果设置为None,则自动生成一个随机id,设置为None是clean_session必须为True
	clean_session:  设置为True时，当客户端断开broker会删除所有关于该客户端的信息.如果为False,客户端断开期间的消息会被保留。
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

	#c = config.config("/root/config.ini")
	#host = c.get("MQTT", "HOST")
	#port = int(c.get("MQTT", "PORT"))
	#user = c.get("MQTT", "USER")
	#passwd = c.get("MQTT", "PASSWD")
	#cafile = c.get("MQTT", "CAFILE")
	
	host="mqtt.iotwonderful.cn"
	port=8883
	user="test_001"
	passwd="NjBlNjY3ZWRlZ"
	cafile="/root/crtfile/mqtt.iotwonderful.cn.crt"

	#logger.info("host={}, port={}, username={}, password={}, cafile={}".format(host, port, user, passwd, cafile))
	mc = mqtt_client(   client_id = device_sn, 
			clean_session = True,
			userdata = None,
			protocol = mqtt.MQTTv31,
			transport = 'tcp')
	mc.set_logger(logger)
	mc.set_device_sn(device_sn)
	mc.setsubscribe(topic=ms.OPENDOOR_TOPIC, qos=0)
	mc.setsubscribe(topic=ms.QR_TOPIC, qos=0)
	mc.setsubscribe(topic=ms.DEVICE_INFO_TOPIC, qos=0)
	mc.setsubscribe(topic=ms.UPDATE_TOPIC, qos=0)
	mc.setsubscribe(topic=ms.OPENSSH_TOPIC, qos=0)
	mc.setsubscribe(topic=ms.WLAN_CONFIG_TOPIC, qos=0)
	mc.set_user_and_password(user, passwd)
	if mc.set_cafile(cafile) == False:
		exit(1)
	time.sleep(0.2)
	if mc.run_mqtt(host=host, port=port, keepalive=10) == False:
		exit(1)
	mc.start_other_thread()
	mc.loop_forever()
