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
	def set_user_and_password(self, username, password):
		self.username = username
		self.password = password

	def set_cafile(self, filename:str)->bool:
		if not os.path.exists(filename):
			print("cafile is not exists")
			exit(1)
		self.cafile = filename

	def set_deviceid(self, devid):
		self.device_sn = devid

	def run(self, host=None, port=1883, keepalive=60):
		self.reconnect_delay_set(min_delay=10, max_delay=120)
		self.username_pw_set(self.username, self.password)
		self.tls_set(ca_certs=self.cafile, certfile=None, keyfile=None, cert_reqs=ssl.CERT_REQUIRED, tls_version=ssl.PROTOCOL_TLSv1_1)
		self.tls_insecure_set(False)
		
		self.connect(host, port, keepalive)
		opendoor = {
			"cmd" : 2,
			"identify" : random.randint(0, 65535),
			"time" : int(time.time())
		}
		
		sendmsg = json.dumps(opendoor)
		topic = "{}{}".format("/acs/ctrl/", self.device_sn)
		self.publish(topic = topic, payload = sendmsg, qos = 0, retain = 0)

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
	time.sleep(0.5)
	mc.run(host=host, port=port, keepalive=60)

