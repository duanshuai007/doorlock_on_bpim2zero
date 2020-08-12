import signal
import os
import config
import time
def signal_handler():
	print("i recv signal")

def test():
	MQTT_CONNECT_SUCCESS_SIG = int(config.config("/root/config.ini").get("SIGNAL", "MQTTCONNOK"))
	pid = os.popen("ps -ef | grep thistest | grep -v grep | awk -F\" \" '{print $2}'")
	pid = int(os.popen("ps -ef | grep test_pysigna | grep -v grep | awk -F\" \" '{print $2}'").read().split('\n')[0])
	os.kill(pid, MQTT_CONNECT_SUCCESS_SIG)
	signal.signal(MQTT_CONNECT_SUCCESS_SIG, signal_handler)

test()

time.sleep(1)
