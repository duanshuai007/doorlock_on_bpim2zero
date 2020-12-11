#!/usr/bin/env python3
#-*- coding:utf-8 -*-


import sys
import os
import logging
import ssl
import paho.mqtt.client as mqtt
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

	def run(self, host=None, port=1883, keepalive=60):
		self.reconnect_delay_set(min_delay=10, max_delay=120)
		self.username_pw_set(self.username, self.password)
		self.tls_set(ca_certs=self.cafile, certfile=None, keyfile=None, cert_reqs=ssl.CERT_OPTIONAL, tls_version=ssl.PROTOCOL_TLSv1_1)
		self.tls_insecure_set(False)
		self.connect(host, port, keepalive)
		opendoor = {
			"cmd" : 2,
			"identif" : random.randint(65545, 95535),
			"time" : int(time.time()),
		}
		sendmsg = json.dumps(opendoor)
		self.publish(topic = '/acs/ask', payload = sendmsg, qos = 0, retain = False)

if __name__ == "__main__":
	host = config.MQTT_SERVER_URL
	port = config.MQTT_SERVER_PORT
	user = config.MQTT_USER
	passwd = config.MQTT_PASSWD
	cafile = config.MQTT_CAFILE_PATH

	print("host={}, port={}, username={}, password={}, cafile={}".format(host, port, user, passwd, cafile))
	mc = mqtt_client(
						clean_session = True,
						userdata = None,
						protocol = mqtt.MQTTv311,
						transport = 'tcp')
	mc.set_user_and_password(user, passwd)
	mc.set_cafile(cafile)
	time.sleep(0.5)
	mc.run(host=host, port=port, keepalive=60)

