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
from threading import Timer

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
	will_subtopic_list = []
	will_unsubtopic_list = []
#	delete_list = []

	wx2vcode = None
	publish_queue = None
	work_queue = None
	status = None
	exit_flag = False
	update_flag = False
	close_door_timer = None
	
	update_status_file = "/home/ubuntu/update_status"
	update_end_file = "/home/ubuntu/update_end"

	cmd_status = {
		"hasCMD" : False,
		"timestamp" : 0,
		"maxwait" : 0,
	}

	mqtt_resp = {
		"resp" : 0,
		"sn" : "",
		"time" : 0,
		"identify" : 0,
		"errorcode" : 0,
	}

	def set_device_sn(self, sn, pid):
		self.mqtt_resp["sn"] = sn
		self.zywlstart_pid = pid
		self.work_queue = queue.Queue(32)
		self.publish_queue = queue.Queue(32)
		self.wx2vcode = wx.wx_2vcode(sn)
		self.screen = sc.screen()
		self.MQTT_CONNECT_SUCCESS_SIG = int(config.config("/root/config.ini").get("SIGNAL", "mqttconnok"))
		self.MQTT_CONNECT_FAILED_SIG = int(config.config("/root/config.ini").get("SIGNAL",  "mqttconnbad"))
		self.MQTT_STATUS_OK_SIG = int(config.config("/root/config.ini").get("SIGNAL",  "mqttstatusok"))
		self.DEVICE_UPDATE_SIG = int(config.config("/root/config.ini").get("SIGNAL", "deviceupdate"))

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
		try:
			if rc == 0:
				if self.exit_flag != True and self.update_flag != True:
					self.logger.info("connect success")
					self.subscribe(self.sub_topic_list)
					
					'''
					send online message
					'''
					self.mqtt_resp["resp"] = ms.MQTT_RESP_ONLINE
					self.mqtt_resp["time"] = int(time.time())
					self.mqtt_resp["identify"] = random.randint(0, 65535)
					respjson = json.dumps(self.mqtt_resp)
					self.publish_queue.put({"topic":ms.RESPONSE_TOPIC, "payload":respjson, 'qos':0, 'retain':True})
					self.publish_queue.put("success")

					if os.path.exists(self.update_status_file):
						with open(self.update_status_file, 'r') as f:
							try:
								line = f.read(32).split('\n')[0]
								result = line.split(':')[0]
								version = line.split(':')[1]
								reason = line.split(':')[2]
								temp_resp = {
									"resp" : 0,
									"time" : int(time.time()),
									"identify" : 0,
									"sn" : self.mqtt_resp["sn"],
									"errorcode" : 0,
								}
								if result == "success":
									#send firmware update success message
									temp_resp["resp"] = self.__get_success_code(ms.MQTT_CMD_UPDATE)
								else:
									temp_resp["resp"] = self.__get_failed_code(ms.MQTT_CMD_UPDATE)
									temp_resp["errorcode"] = int(reason)
								sendmsg = json.dumps(temp_resp)
								self.publish_queue.put({"topic":ms.RESPONSE_TOPIC, "payload":sendmsg, 'qos':2, 'retain':False})
							except Exception as e:
								self.logger.error("read update status file error:{}".format(e))
						os.remove(self.update_status_file)
					if os.path.exists(self.update_end_file):
						os.remove(self.update_end_file)
		except Exception as e:
			self.logger.error("on_connect error:{}".format(e))

	#执行mqttc.disconnect()主动断开连接会触发该函数
	#当因为什么原因导致客户端断开连接时也会触发该函数,ctrl-c停止程序不会触发该函数
	def on_disconnect(self, mqttc, obj, rc):
		self.publish_queue.put("failed")
		self.logger.info("on_disconnect obj={}, rc={}".format(obj, rc))
		time.sleep(1)
		mqttc.reconnect()

	'''
	mqttc:	the client instance for this callback
	obj:	the private user data as set in ``Client()`` or ``user_data_set()``
	msg:	an instance of MQTTMessage. This is a class with members ``topic``, ``payload``, ``qos``, ``retain``.
	'''
	def on_message(self, mqttc, obj, msg):
		try:
			if self.exit_flag != True and self.update_flag != True:
				json_msg = json.loads(str(msg.payload, encoding="utf-8"))
				self.logger.info("on message:" + msg.topic + " " + str(msg.qos) + " " + str(msg.payload))
				local_time = int(time.time())
				recv_time = int(json_msg["time"])
				if (abs(local_time - recv_time) < 20):
					if self.work_queue is not None:
						self.work_queue.put(json_msg)
						if self.cmd_status["hasCMD"] == False:
							self.cmd_status["hasCMD"] = True
							self.cmd_status["timestamp"] = local_time
							self.cmd_status["maxwait"] = 5
				else:
					#timeout, message lost
					self.logger.warn("on message: this message timestamp was timeout")
					self.mqtt_resp["resp"] = self.__get_failed_code(json_msg["cmd"])
					self.mqtt_resp["errorcode"] = ms.MQTT_RESP_TIMEOUT
					self.mqtt_resp["time"] = int(time.time())
					self.mqtt_resp["identify"] = json_msg["identify"]
					respmsg = json.dumps(self.mqtt_resp)
					self.publish_queue.put({"topic":ms.RESPONSE_TOPIC, "payload":respmsg, 'qos':0, 'retain':False})
					pass
		except Exception as e:
			self.logger.error("on message exception:{}".format(e))

	def on_publish(self, mqttc, obj, mid):
		#重要，用来确认publish的消息发送出去了。有时即使publish返回成功，但消息却没有发送。
#		for item in self.delete_list:
#			if mid == item["mid"]:
#				self.logger.info("on publish remove msg, mid={}".format(mid))
#				self.delete_list.remove(item)
		pass

	def on_subscribe(self, mqttc, obj, mid, granted_qos):
		self.logger.info("Subscribed: " + " " + str(mid) + " " + str(granted_qos))
		try:
			for item in self.will_subtopic_list:
				if item["mid"] == mid:
					self.will_subtopic_list.remove(item)
					self.logger.info("subscribe success")
					self.mqtt_resp["resp"] = self.__get_success_code(ms.MQTT_CMD_SET_GROUP)
					self.mqtt_resp["time"] = int(time.time())
					respmsg = json.dumps(self.mqtt_resp)
					self.publish_queue.put({"topic":ms.RESPONSE_TOPIC, "payload":respmsg, 'qos':0, 'retain':False})
		except Exception as e:
			self.logger.error("on_subscribe error:{}".format(e))
	
	def on_unsubscribe(self, mqttc, obj, mid):
		self.logger.info("UnSubscribed: " + " " + str(mid))
		try:
			for item in self.will_unsubtopic_list:
				if item["mid"] == mid:
					self.will_unsubtopic_list.remove(item)
					self.logger.info("unsubscribe success")
					self.mqtt_resp["resp"] = self.__get_success_code(ms.MQTT_CMD_SET_GROUP)
					self.mqtt_resp["time"] = int(time.time())
					respmsg = json.dumps(self.mqtt_resp)
					self.publish_queue.put({"topic":ms.RESPONSE_TOPIC, "payload":respmsg, 'qos':0, 'retain':False})
		except Exception as e:
			self.logger.error("on_unsubscribe error:{}".format(e))

	'''
	def on_log(self, mqttc, obj, level, string):
		self.logger.info(string)
	'''

	def setsubscribe(self, topic=None, qos=0):
		self.sub_topic_list.append((topic, qos))

	def __timer_for_doorlockctl(self):
		spilcd_api.set_doorlock(self.DOORLOCK_LEVEL)
		self.logger.info("door lock close!")

	def publish_threading(self):
		while True:
			try:
				if not self.publish_queue.empty():
					msg = self.publish_queue.get()
					self.logger.info("publish_queue get a message")
					if isinstance(msg, dict) == True:
						info = self.publish(topic = msg["topic"], payload = msg["payload"], qos = msg["qos"], retain = msg["retain"])
						if info.rc == mqtt.MQTT_ERR_SUCCESS:
							info.wait_for_publish()
						if self.cmd_status["hasCMD"] == True:
							self.cmd_status["hasCMD"] = False
						os.kill(self.zywlstart_pid, self.MQTT_STATUS_OK_SIG)
					else:
						if msg == "success":
							self.logger.info("send mqtt connect success signal:{} to {}".format(self.MQTT_CONNECT_SUCCESS_SIG, self.zywlstart_pid))
							os.kill(self.zywlstart_pid, self.MQTT_CONNECT_SUCCESS_SIG)
						else:
							self.logger.info("send mqtt connect failed signal:{} to {}".format(self.MQTT_CONNECT_FAILED_SIG, self.zywlstart_pid))
							os.kill(self.zywlstart_pid, self.MQTT_CONNECT_FAILED_SIG)
				time.sleep(0.1)
			except queue.Empty:
				self.logger.warn("publish_threading not get queue message")
			except Exception as e:
				self.logger.error("publish_threading error:{}".format(e))

	def __send_online_message_to_server(self):
		self.mqtt_resp["resp"] = 100
		sendmsg = json.dumps(self.mqtt_resp)
		self.publish_queue.put({"topic":ms.RESPONSE_TOPIC, "payload":sendmsg, 'qos':0, 'retain':False})
		
	def __conctrl_door_and_response(self):
		try:
			#执行开锁动作,返回动作响应信息
			self.DOORLOCK_LEVEL = int(config.config("/root/config.ini").get("DOORLOCK", "CLOSE_LEVEL"))
			DOORLOCK_TIME = int(config.config("/root/config.ini").get("DOORLOCK", "OPEN_TIME"))
			#高电平门锁断电，能够打开
			gpio_val = 1 - self.DOORLOCK_LEVEL
			if self.close_door_timer is not None:
				if self.close_door_timer.isAlive() == True:
					self.close_door_timer.cancel()
					self.close_door_timer.join()
			self.close_door_timer = Timer(DOORLOCK_TIME, self.__timer_for_doorlockctl)
			self.close_door_timer.setDaemon(True)
			self.close_door_timer.start()
			spilcd_api.set_doorlock(gpio_val)
			self.mqtt_resp["resp"] = self.__get_success_code(ms.MQTT_CMD_OPENDOOR)
			sendmsg = json.dumps(self.mqtt_resp)
			self.publish_queue.put({"topic":ms.RESPONSE_TOPIC, "payload":sendmsg, 'qos':0, 'retain':False})
		except Exception as e:
			self.logger.error("__conctrl_door_and_response error:{}".format(e))

	def __device_upgrade(self, json_msg:dict):
		try:
			self.update_flag = True
			version = int(config.config("/root/config.ini").get("FIRMWARE", "VERSION"))
			update_version = int(json_msg["message"]["version"])
			temp_resp = {
				"sn" : self.mqtt_resp["sn"],
				"identify" : self.mqtt_resp["identify"],
				"time" : int(time.time()),
			}
			if version >= update_version:
				#当前版本高于等待升级的版本，不升级
				temp_resp["resp"] = self.__get_failed_code(json_msg["cmd"])
				temp_resp["errorcode"] = ms.MQTT_UPGRADE_IGNORE
				sendmsg = json.dumps(temp_resp)
				self.publish_queue.put({"topic":ms.RESPONSE_TOPIC, "payload":sendmsg, 'qos':0, 'retain':False})
			else:
				#当前版本低于等待升级的版本，进行升级
				temp_resp["resp"] = self.__get_success_code(json_msg["cmd"])
				temp_resp["errorcode"] = ms.MQTT_UPGRADE_READY
				sendmsg = json.dumps(temp_resp)
				self.publish_queue.put({"topic":ms.RESPONSE_TOPIC, "payload":sendmsg, 'qos':0, 'retain':False})
				md5str = json_msg["message"]["md5"]
				download_url = json_msg["message"]["url"]
				filename = "/home/download/firmware_{}.des3.tar.gz".format(json_msg["message"]["version"])
				if downloadtool.download_firmware(download_url, md5str, filename) == True:
					temp_resp["resp"] = self.__get_success_code(json_msg["cmd"])
					temp_resp["errorcode"] = ms.MQTT_UPGRADE_DOWNLOAD
					temp_resp["time"] = int(time.time())
					sendmsg = json.dumps(temp_resp)
					self.publish_queue.put({"topic":ms.RESPONSE_TOPIC, "payload":sendmsg, 'qos':0, 'retain':False})
					time.sleep(0.5)
					with open(self.update_status_file, "w") as f:
						update_message="{}:{}:0".format("start", update_version)
						f.write(update_message)
					os.kill(self.zywlstart_pid, self.DEVICE_UPDATE_SIG)
				else:
					temp_resp["resp"] = self.__get_failed_code(json_msg["cmd"])
					temp_resp["errorcode"] = ms.MQTT_UPGRADE_DOWNLOAD
					temp_resp["time"] = int(time.time())
					sendmsg = json.dumps(temp_resp)
					self.publish_queue.put({"topic":ms.RESPONSE_TOPIC, "payload":sendmsg, 'qos':0, 'retain':False})
					self.update_flag = False
		except Exception as e:
			self.logger.error("__device_upgrade error:{}".format(e))
	
	def __device_open_ssh(self, json_msg:dict):
		try:
			if json_msg["cmd"] == ms.MQTT_CMD_OPENSSH_CLOSE:
				cmd = "service frpc stop"
				os.system(cmd)
			else:	#open ssh
				cmd = "service frpc start"
				os.system(cmd)
			self.mqtt_resp["resp"] = self.__get_success_code(json_msg["cmd"])
			sendmsg = json.dumps(self.mqtt_resp)
			self.publish_queue.put({"topic":ms.RESPONSE_TOPIC, "payload":sendmsg, 'qos':0, 'retain':False})
		except Exception as e:
			self.logger.error("__device_open_ssh error:{}".format(e))

	def __set_device_wlan(self, json_msg:dict):
		try:
			with open("/root/net.conf", "r") as f:
				s = f.readline()
			with open("/root/net.conf", "w") as f:
				f.write("{}ssid={}\npsk={}\n".format(s, json_msg["message"]["ssid"], json_msg["message"]["psk"]))
			self.mqtt_resp["resp"] = self.__get_success_code(json_msg["cmd"])
			sendmsg = json.dumps(self.mqtt_resp)
			self.publish_queue.put({"topic":ms.RESPONSE_TOPIC, "payload":sendmsg, 'qos':0, 'retain':False})
		except Exception as e:
			self.logger.error("__set_device_wlan error:{}".format(e))
	
	def __set_doorlock_time(self, json_msg:dict):
		try:
			ret = config.config("/root/config.ini").set("DOORLOCK", "OPEN_TIME", str(json_msg["message"]["config"]))
			if ret == True:
				self.mqtt_resp["resp"] = self.__get_success_code(json_msg["cmd"])
			sendmsg = json.dumps(self.mqtt_resp)
			self.publish_queue.put({"topic":ms.RESPONSE_TOPIC, "payload":sendmsg, 'qos':0, 'retain':False})
		except Exception as e:
			self.logger.error("__set_doorlock_time error:{}".format(e))
	
	def __device_add_or_sub_group(self, json_msg:dict):
		try:
			if "set" in json_msg["message"].keys():
				setstr = json_msg["message"]["set"]
				#"6,0;7,1;8,2"
				idlist = setstr.split(';')
				subtopic = []
				for gid in idlist:
					if len(gid) == 0:
						continue
					temp = gid.split(',')
					topic = "{}{}".format(ms.CONCTRL_TOPIC_HEAD, temp[0])
					self.logger.info("new sub topic:{}, qos:{}".format(topic, temp[1]))
					subtopic.append((topic, int(temp[1])))
				info = self.subscribe(subtopic)
				self.will_subtopic_list.append({"mid":info[1], "topiclist":subtopic, "time":int(time.time())})
			if "unset" in json_msg["message"].keys():
				setstr = json_msg["message"]["unset"]
				idlist = setstr.split(',')
				unsubtopic = []
				for gid in idlist:
					if len(gid) == 0:
						continue
					topic = "{}{}".format(ms.CONCTRL_TOPIC_HEAD,  gid)
					self.logger.info("unsub topic:{}".format(topic))
					unsubtopic.append(topic)
				info = self.unsubscribe(unsubtopic)
				self.will_unsubtopic_list.append({"mid":info[1], "topiclist":unsubtopic, "time":int(time.time())})
		except Exception as e:
			self.logger.error("__device_add_or_sub_group error:{}".format(e))

	def __get_device_wlan(self):
		try:
			tmp_resp = {
				"sn" : self.mqtt_resp["sn"],
				"identify" : self.mqtt_resp["identify"],
				"time" : int(time.time()),
				"device" : {
					"current" : "",
					"ip" : "",
					"ssid" : "",
					"psk" : "",
				}
			}
			with open("/tmp/current_network", 'r') as f:
				line = f.readline().split(":")
				tmp_resp["device"]["current"] = line[0]
				tmp_resp["device"]["ip"] = line[1].split('\n')[0]
			with open("/root/net.conf", 'r') as f:
				while True:
					line = f.readline()
					if len(line) == 0:
						break
					else:
						line = line.split('\n')[0]
						if line is not None:
							if line.startswith("ssid="):
								tmp_resp["device"]["ssid"] = line.split("=")[1]
							if line.startswith("psk="):
								tmp_resp["device"]["psk"] = line.split("=")[1]
			sendmsg = json.dumps(tmp_resp)
			self.publish_queue.put({"topic":ms.RESPONSE_TOPIC, "payload":sendmsg, 'qos':0, 'retain':False})
		except Exception as e:
			self.logger.error("__get_device_wlan error:{}".format(e))

	def do_hardware_work(self):
		spilcd_api.on()
		while True:
			try:
				if not self.work_queue.empty():
					json_msg = self.work_queue.get()
					#self.work_queue.task_done()
					cmd = json_msg["cmd"]
					self.logger.info("do_hardware_work:cmd={}".format(cmd))
					self.mqtt_resp["resp"] = self.__get_failed_code(cmd);
					self.mqtt_resp["identify"] = json_msg["identify"]
					self.mqtt_resp["time"] = int(time.time())
					if cmd == ms.MQTT_CMD_CHECKSTATUS:
						self.__send_online_message_to_server()
					elif cmd == ms.MQTT_CMD_OPENDOOR:
						self.__conctrl_door_and_response()
					elif cmd == ms.MQTT_CMD_QR_BY_WX:
						#执行显示二维码动作,该动作不需要返回响应信息
						self.cmd_status["maxwait"] = 30
						filepath = self.wx2vcode.get_2vcode(json_msg["message"])
						#self.logger.info("wx2ccode ret = {}".format(filepath))
						if filepath is not None:
							#self.logger.info("filepath = {}".format(filepath))
							ret = self.screen.show_image_on_screen(filepath, True, True)
							if ret == True:
								self.mqtt_resp["resp"] = self.__get_success_code(cmd)
						self.mqtt_resp["time"] = int(time.time())
						sendmsg = json.dumps(self.mqtt_resp)
						self.publish_queue.put({"topic":ms.RESPONSE_TOPIC, "payload":sendmsg, 'qos':0, 'retain':False})
					elif cmd == ms.MQTT_CMD_QR_DOWNLOAD:
						self.cmd_status["maxwait"] = 30
						ret = self.screen.down_image_and_show_image_on_screen(json_msg["message"])
						if ret == True:
							self.mqtt_resp["resp"] = self.__get_success_code(cmd)
						self.mqtt_resp["time"] = int(time.time())
						sendmsg = json.dumps(self.mqtt_resp)
						self.publish_queue.put({"topic":ms.RESPONSE_TOPIC, "payload":sendmsg, 'qos':0, 'retain':False})
					elif cmd == ms.MQTT_CMD_QR_BY_SELF:
						self.cmd_status["maxwait"] = 10
						ret = self.screen.show_qrcode_2vcode_on_screen(json_msg["message"])
						if ret == True:
							self.mqtt_resp["resp"] = self.__get_success_code(cmd)
						self.mqtt_resp["time"] = int(time.time())
						sendmsg = json.dumps(self.mqtt_resp)
						self.publish_queue.put({"topic":ms.RESPONSE_TOPIC, "payload":sendmsg, 'qos':0, 'retain':False})
					elif cmd == ms.MQTT_CMD_SET_GROUP:
						self.__device_add_or_sub_group(json_msg)
					elif cmd == ms.MQTT_CMD_SET_DOORLOCKTIME:
						self.__set_doorlock_time(json_msg)
					elif cmd == ms.MQTT_CMD_UPDATE:
						self.cmd_status["maxwait"] = 60
						self.__device_upgrade(json_msg)
					elif cmd == ms.MQTT_CMD_OPENSSH_OPEN or cmd == ms.MQTT_CMD_OPENSSH_CLOSE:
						self.__device_open_ssh(json_msg)
					elif cmd == ms.MQTT_CMD_SETWLAN:
						self.__set_device_wlan(json_msg)
					elif cmd == ms.MQTT_CMD_GETWLAN:
						self.__get_device_wlan()
					else:
						self.logger.info("invaild cmd = {}".format(cmd))
						self.mqtt_resp["errorcode"] = ms.MQTT_RESP_INVAILD
						sendmsg = json.dumps(self.mqtt_resp)
						self.publish_queue.put({"topic":ms.RESPONSE_TOPIC, "payload":sendmsg, 'qos':0, 'retain':False})
				time.sleep(0.1)
			except queue.Empty:
				self.logger.warn("hardware thread not get queue message")
			except Exception as e:
				self.logger.error("hardware thread except:{}".format(e))
	
	def mnonitor_threading(self):
		while True:
			try:
				if self.cmd_status["hasCMD"] == True:
					cur = int(time.time())
					if cur - self.cmd_status["timestamp"] >= self.cmd_status["maxwait"]:
						self.logger.info("monitor find cmd timeout, send failed signal:{} to zywlstart.sh:{}".format(self.MQTT_CONNECT_FAILED_SIG, self.zywlstart_pid))
						os.kill(self.zywlstart_pid, self.MQTT_CONNECT_FAILED_SIG)
				cur = int(time.time())
				for item in self.will_subtopic_list:
					if cur - item["time"] > 5:
						self.mqtt_resp["resp"] == self.__get_failed_code(ms.MQTT_CMD_SET_GROUP)
						self.mqtt_resp["time"] = int(time.time())
						respmsg = json.dumps(self.mqtt_resp)
						self.publish_queue.put({"topic":ms.RESPONSE_TOPIC, "payload":respmsg, 'qos':0, 'retain':False})
						self.will_subtopic_list.remove(item)
					#self.subscribe(item["topiclist"])
				for item in self.will_unsubtopic_list:
					if cur - item["time"] > 5:
						self.mqtt_resp["resp"] == self.__get_failed_code(ms.MQTT_CMD_SET_GROUP)
						self.mqtt_resp["time"] = int(time.time())
						respmsg = json.dumps(self.mqtt_resp)
						self.publish_queue.put({"topic":ms.RESPONSE_TOPIC, "payload":respmsg, 'qos':0, 'retain':False})
						self.will_unsubtopic_list.remove(item)
					#self.unsubscribe(item["topiclist"])
				time.sleep(5)
			except Exception as e:
				self.logger.error("monitor thread except:{}".format(e))

	def start_other_thread(self):
		self.hardware_thread = threading.Thread(target = self.do_hardware_work)
		self.hardware_thread.setDaemon(True)
		self.hardware_thread.start()
		self.publish_thread = threading.Thread(target = self.publish_threading)
		self.publish_thread.setDaemon(True)
		self.publish_thread.start()
		self.monitor_myself = threading.Thread(target = self.mnonitor_threading)
		self.monitor_myself.setDaemon(True)
		self.monitor_myself.start()

	def __get_failed_code(self, cmd:int):
		return 100 + (cmd * 2) - 1

	def __get_success_code(self, cmd:int):
		return 100 + (cmd * 2) - 2

	def exit_handler(self, signum, frame):
		self.exit_flag = True

	def run_mqtt(self, host=None, port=1883, keepalive=60):
		try:
			self.exit_flag = False
			self.exit_signal = int(config.config("/root/config.ini").get("SIGNAL", "EXITFLAG"))
			signal.signal(self.exit_signal, self.exit_handler)

			self.mqtt_resp["resp"] = ms.MQTT_RESP_OFFLINE
			self.mqtt_resp["time"] = int(time.time())
			self.mqtt_resp["identify"] = random.randint(0, 65535)
			respjson = json.dumps(self.mqtt_resp)
			self.will_set(topic=ms.RESPONSE_TOPIC, payload=respjson, qos=0, retain=True)
			self.reconnect_delay_set(min_delay=10, max_delay=60)
			#logging.basicConfig(level=logging.INFO)
			#self.logger = logging.getLogger(__name__)
			self.connect(host, port, keepalive)
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
	if len(sys.argv) < 3:
		print("paramter must be 3")
		exit(1)
	device_sn = sys.argv[1]
	zywlstart_pid = int(sys.argv[2])

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
	mc.set_device_sn(device_sn, zywlstart_pid)
	
	private_ctrl_topic = "{}{}".format(ms.CONCTRL_TOPIC_HEAD, device_sn)
	mc.setsubscribe(topic=private_ctrl_topic, qos=0)	
	mc.setsubscribe(topic=ms.COMMON_TOPIC, qos=0)

	mc.set_user_and_password(user, passwd)
	if mc.set_cafile(cafile) == False:
		exit(1)
	time.sleep(0.2)
	if mc.run_mqtt(host=host, port=port, keepalive=20) == False:
		exit(1)
	mc.start_other_thread()
	mc.loop_forever()
