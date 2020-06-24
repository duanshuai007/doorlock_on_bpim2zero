import spilcd_api
import time

spilcd_api.on()

while True:
	spilcd_api.set_doorlock(1)
	time.sleep(1)
	spilcd_api.set_doorlock(0)
	time.sleep(1)
