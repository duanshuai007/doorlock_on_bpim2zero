import spilcd_api
import time

spilcd_api.on()

while True:
	spilcd_api.set_doorlock_open()
	time.sleep(1)
	spilcd_api.set_doorlock_close()
	time.sleep(1)
