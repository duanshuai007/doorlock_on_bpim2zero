
import serial
import os

s = serial.Serial("/dev/ttyS2", 115200, 8, serial.PARITY_NONE, 1, 0.5)
while True:
	msg = s.read(128)
	print(msg)

