#!/usr/bin/env python3
#-*- coding:utf-8 -*-

import serial
import os
import time

s = serial.Serial("/dev/ttyS2", 115200, 8, serial.PARITY_NONE, 1, 0.5)

s.write(bytes("AT\r".encode('utf-8')));
msg=s.read(128)
if "OK" in str(msg):
	cmd="echo \"OK\" > /tmp/serial"
else:
	cmd="echo \"FAIL\" > /tmp/serial"

os.system(cmd);
