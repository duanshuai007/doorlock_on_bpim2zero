#!/usr/bin/env python3
#-*- coding:utf-8 -*-


import sys
import os
import logging
import ssl
import paho.mqtt.client as mqtt

final_mid = 0

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def on_connect(mqttc, obj, flags, rc):
	print("on connect")
	if obj == True:
		print("rc: " + str(rc))

#执行mqttc.disconnect()主动断开连接会触发该函数
def on_disconnect(mqttc, obj, rc):
	mqttc.user_data_set(obj + 1)
	if obj == 0:
		mqttc.reconnect()

def on_message(mqttc, obj, msg):
	print("on message:" + msg.topic + " " + str(msg.qos) + " " + str(msg.payload))
	global final_mid
	if msg.retain == 0:
		print("retain msg:")
		print(msg)
	else:
		if obj == True:
			print("Clearing topic " + msg.topic)
		(rc, final_mid) = mqttc.publish(msg.topic, None, 1, True)

def on_publish(mqttc, obj, mid):
	global final_mid
	print("on public")
	if mid == final_mid:
		sys.exit()

def on_subscribe(mqttc, obj, mid, granted_qos):
	print("Subscribed: " + str(mid) + " " + str(granted_qos))

def on_log(mqttc, obj, level, string):
	print(string)


def main():
	global logger
	debug = True
	host = "mq.tongxinmao.com"
	client_id = "duan_19870209"
	keepalive = 60
	port = 18830
	username = None
	password = None
	topic = "/public/TEST/duan"
	verbose = False

	usetls = None
	secure = None

	mqttc = mqtt.Client(client_id, clean_session = False)
	#will message will send to mqtt server when client disconnect
	mqttc.will_set('/public/TEST/duan/will', "test will message!", 2, False)
	mqttc.enable_logger(logger)

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
#	mqttc.tls_insecure_set(True)

	mqttc._obj = verbose
	mqttc.on_message = on_message
	mqttc.on_publish = on_publish
	mqttc.on_connect = on_connect
	mqttc.on_disconnect = on_disconnect
	mqttc.on_subscribe = on_subscribe
	if debug:
		mqttc.on_log = on_log

	#if username:
	mqttc.username_pw_set(username, password)
	mqttc.connect(host, port, keepalive)
	mqttc.subscribe(topic)
	mqttc.loop_forever()

if __name__ == "__main__":
	main()
