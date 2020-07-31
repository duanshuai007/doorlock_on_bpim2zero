#!/usr/bin/env python3
#-*- coding:utf-8 -*-

import serial
import os

test_phonenumber="18642224555"

s = serial.Serial("/dev/ttyS2", 115200, 8, serial.PARITY_NONE, 1, 0.5)
'''
s.write(bytes("AT\r".encode('utf-8')));
msg=s.read(128)
if "OK" in str(msg):
	cmd="echo \"OK\" > /tmp/serial"
else:
	cmd="echo \"FAIL\" > /tmp/serial"
'''
s.write(bytes("AT\r".encode('utf-8')));
msg=s.read(128)
if msg == b'':
	print("sim modules error")
	exit(1)
s.write(bytes("AT+CPBS=\"ON\"\r".encode('utf-8')))
msg=s.read(128)
atcmd="AT+CPBW=1,\"{}\"\r".format(test_phonenumber)
s.write(bytes(atcmd.encode('utf-8')))
msg=s.read(128)
s.write(bytes("AT+CNUM\r".encode('utf-8')))
msg=s.read(128)
#print(msg)
if msg == b'':
	print("not find vaild sim card")
	exit(1)
msgstr=str(msg, encoding="utf-8").split("\r\n")[1]
#print(msgstr)

if "18642224555" in msgstr:
	print("sim card is ok!")
	cmd = "echo \"OK\" > /tmp/serial"
else:
	cmd="echo \"FAIL\" > /tmp/serial"

os.system(cmd)
