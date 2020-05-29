import bpim2zero_gpio
import time

#以下为主程序
gpio = bpim2zero_gpio.GPIO()

'''
val = GPIO.ReadReg(GPIO.PIO_PA_CFG0_REG)
#PA3 SET OUTPUT
GPIO.WriteReg(GPIO.PIO_PA_CFG0_REG, val | 0x00001000)
while(1):
	GPIO.WriteReg(GPIO.PIO_PA_DATA_REG, GPIO.ReadReg(GPIO.PIO_PA_DATA_REG) ^ 0x00000008)
	time.sleep(0.3)
'''

gpio.setPinFunc("gpioa", 3, "output")
v = gpio.readPin("gpioa", 3)
print("read val = {}".format(v))

while True:
	gpio.writePin("gpioa", 3, 0)
	time.sleep(3)
	gpio.writePin("gpioa", 3, 1)
	time.sleep(3)

