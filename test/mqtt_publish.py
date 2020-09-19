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

def initLogging(logFilename):
	logging.basicConfig(
			level = logging.INFO,
			format ='%(asctime)s-%(levelname)s-%(message)s',
			datefmt = '%y-%m-%d %H:%M',
			filename = logFilename,
			filemode = 'a')

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
		#print(time.strftime("[%Y-%m-%d %H:%M:%S]", time.localtime()) + ":on message:" + msg.topic + " " + str(msg.qos) + " " + str(msg.payload))
		try:
			msgstr = str(msg.payload, encoding='utf-8')
			msgjson = json.loads(msgstr)
			if msg.topic == "/qr_response":
				if msgjson["status"] == 1:
					print(time.strftime("[%m-%d %H:%M:%S]", time.localtime()) + ":device:[{}] qrcode contrl success".format(msgjson["device_sn"]))
					pass
				else:
					print(time.strftime("[%m-%d %H:%M:%S]", time.localtime()) + ":device:[{}] qrcode contrl error".format(msgjson["device_sn"]))
			elif msg.topic == "/door_response":
				if msgjson["result"] == 1:
					#print(time.strftime("[%m-%d %H:%M:%S]", time.localtime()) + ":device:[{}] open door success".format(msgjson["device_sn"]))
					pass
				else:
					print(time.strftime("[%m-%d %H:%M:%S]", time.localtime()) + ":device:[{}] open door failed".format(msgjson["device_sn"]))
			elif msg.topic.startswith("/status/"):
				if msgjson["status"] == 0:
					print(time.strftime("[%m-%d %H:%M:%S]", time.localtime()) + ":device:[{}] offline".format(msg.topic[8:]))
				else:
					print(time.strftime("[%m-%d %H:%M:%S]", time.localtime()) + ":device:[{}] online".format(msg.topic[8:]))
			elif msg.topic == "/test/device_info_resp":
				print(time.strftime("[%m-%d %H:%M:%S]", time.localtime()) + ":device[{}] current:{} ip:{} doorlock:{}".format(msgjson["device_sn"], msgjson["current"], msgjson["ip"], msgjson["doorlock"]))
			elif msg.topic == "/ssh_enable_resp":
				if msgjson["status"] == "open":
					print(time.strftime("[%m-%d %H:%M:%S]", time.localtime()) + ":device[{}] open frpc service".format(msgjson["device_sn"]))
				else:
					print(time.strftime("[%m-%d %H:%M:%S]", time.localtime()) + ":device[{}] close frpc service".format(msgjson["device_sn"]))
			elif msg.topic == "/update_resp":
				print(time.strftime("[%m-%d %H:%M:%S]", time.localtime()) + ":device[{}]:update status[{}] version[{}]".format(msgjson["device_sn"], msgjson["firmware"]["status"], msgjson["firmware"]["version"]))
			else:
				print(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()) + ":on message:" + msg.topic + " " + str(msg.qos) + " " + str(msg.payload))
					
		except Exception as e:
			print("on message exception:{}".format(e))

	def on_publish(self, mqttc, obj, mid):
		#重要，用来确认publish的消息发送出去了。有时即使publish返回成功，但消息却没有发送。
		pass

	def on_subscribe(self, mqttc, obj, mid, granted_qos):
		print("Subscribed: " + str(mid) + " " + str(granted_qos))
	
	def setsubscribe(self, topic=None, qos=0):
		self.sub_topic_list.append((topic, qos))

	def run(self, host=None, port=1883, keepalive=60):
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

	host = "mqtt.iotwonderful.cn"
	port = 8883
	user = "test_001"
	passwd = "NjBlNjY3ZWRlZ"
	cafile = "./.mqtt.iotwonderful.cn.crt"
	crtfile= ''' 
-----BEGIN CERTIFICATE-----
MIIEATCCAumgAwIBAgIJAJueN6AjXSA0MA0GCSqGSIb3DQEBCwUAMIGWMQswCQYD
VQQGEwJDTjEQMA4GA1UECAwHQmVpamluZzEQMA4GA1UEBwwHQmVpamluZzEVMBMG
A1UECgwMSW90V29uZGVyZnVsMQwwCgYDVQQLDANQcmQxFTATBgNVBAMMDGlvdHdv
bmRlcmZ1bDEnMCUGCSqGSIb3DQEJARYYd3VzaHVhaUBpb3R3b25kZXJmdWwuY29t
MB4XDTIwMDYwOTA3MDcwNVoXDTMwMDYwNzA3MDcwNVowgZYxCzAJBgNVBAYTAkNO
MRAwDgYDVQQIDAdCZWlqaW5nMRAwDgYDVQQHDAdCZWlqaW5nMRUwEwYDVQQKDAxJ
b3RXb25kZXJmdWwxDDAKBgNVBAsMA1ByZDEVMBMGA1UEAwwMaW90d29uZGVyZnVs
MScwJQYJKoZIhvcNAQkBFhh3dXNodWFpQGlvdHdvbmRlcmZ1bC5jb20wggEiMA0G
CSqGSIb3DQEBAQUAA4IBDwAwggEKAoIBAQC4Wjj7eziKCl1bESQUumO0Er00a9YW
vMC4zR3v63esqbthjN5mqP0zd30Z5uVyn0dzum0a1Un7WlIdsaEQUW5HcixfmUDc
sBVep0XmmWxtuVzMUpPVRVWUtIbagL8RJjx2cpb33w2t2lDxh5Gj7phZTPDDlyI6
OSSjauUlv1mOpkHcDBi0iU/wqUXUEo7hsBUft/6uMQK27HXlGn8TvgRT1oXFEVZo
HvPf9sDRjDxV39iNEhUKRHX2dxxsgLbA6IqI1W2k0h+WVnafp7hjy9QCbjRkBGWK
1HJ/HqICNBv+UTURsn7DFDioEcuFELGFf0m9Z5nVT7O7Pek10Q7BVBivAgMBAAGj
UDBOMB0GA1UdDgQWBBS7sWlXl0ZdB5LXA9/TCmk9mdVwRzAfBgNVHSMEGDAWgBS7
sWlXl0ZdB5LXA9/TCmk9mdVwRzAMBgNVHRMEBTADAQH/MA0GCSqGSIb3DQEBCwUA
A4IBAQBKw3odroL+BPLewpskJ228+PqqvSQvC3MwMfRA9r6rvIGqQmlW8Utj0Gux
x7MiDo9wgj61DnndbrSac/oJ5icT8gI7suKeCSh23eLQ58MxZuJzYCekT2s4qVAi
VLbeb7b4iQadlt3TeIjzvvj60qEHq4Md0SOf1gc01tGc6fMW7Ql29P4RdD682Xad
KaSWcB3N/NRGZ0zW9321tUgN6VKOEOWqt4vt9G2mPViLeUH7ZVB1gor+pR4N6ljG
C0FvxTyyS61Jgy/zDfPidUOGCUGukl67T5xQjlewckKnyrTORLDIvMgvLdyD3y2U
tXfw8qEIFXkmqPXch2AyF5Jq6iTE
-----END CERTIFICATE-----
	'''

	if not os.path.exists(cafile):
		with open(cafile, "w") as w:
			w.write(crtfile)
	initLogging("./mqtt_file.log")
	
	print("host={}, port={}, username={}, password={}, cafile={}".format(host, port, user, passwd, cafile))
	mc = mqtt_client(	client_id = "id_shenyang_test_all_subscribe111", 
						clean_session = False,
						userdata = None,
						protocol = mqtt.MQTTv31,
						transport = 'tcp')
	mc.setsubscribe(topic='/acs_open', qos=0)
	mc.setsubscribe(topic='/qr_code', qos=0)
	mc.setsubscribe(topic='/door_response', qos=0)
	mc.setsubscribe(topic='/qr_response', qos=0)
	mc.setsubscribe(topic="/status", qos=0)
	mc.setsubscribe(topic="/test/device_info_resp", qos=0)
	mc.setsubscribe(topic="/update_resp", qos=0)
	mc.setsubscribe(topic="/ssh_enable_resp", qos=0)
	with open("./device_sn.table", "r") as f:
		while True:
			linemsg = f.readline().split('\n')[0]
			if len(linemsg) == 0:
				break
			print(linemsg)
			device_status_topic = "{}/{}".format("/status", linemsg)
			mc.setsubscribe(topic=device_status_topic, qos=0)
		
	mc.set_user_and_password(user, passwd)
	mc.set_cafile(cafile)
	mc.run(host=host, port=port, keepalive=60)

