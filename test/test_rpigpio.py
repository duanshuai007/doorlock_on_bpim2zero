import RPi.GPIO as gpio
import time

gpio.setmode(gpio.BCM)

gpio.setup(12, gpio.OUT)
while True:
	gpio.output(12, True)
	time.sleep(1)
	gpio.output(12, False)
	time.sleep(1)
