#!/usr/bin/env python3
#-*- coding:utf-8 -*-

import serial
import os
import sys
import time
import shutil
import threading
import signal
import config

class check_ttys2isok():

	uart = None
	exit_flag = False
	power_pin = 3
	zywlstart_pid = 0
	sim_module_error = 0

	def open_serial(self):
		self.uart = serial.Serial("/dev/ttyS2", 115200, 8, serial.PARITY_NONE, 1, 0.5)
		if self.uart is None:
			print("open ttyS2 failed")
			return False
		#do gsm module power up	
		if not os.path.exists("/sys/class/gpio/gpio{}".format(self.power_pin)):
			shell_cmd_string = "echo {} > /sys/class/gpio/export".format(self.power_pin)
			#print(shell_cmd_string)
			os.system(shell_cmd_string)
			shell_cmd_string = "echo out > /sys/class/gpio/gpio{}/direction".format(self.power_pin)
			#print(shell_cmd_string)
			os.system(shell_cmd_string)
		#power down 因为在电路上做了取反，所以对应的控制电平就是反的
		shell_cmd_string = "echo 0 > /sys/class/gpio/gpio{}/value".format(self.power_pin)
		#print(shell_cmd_string)
		os.system(shell_cmd_string)
		time.sleep(2)
		
		shell_cmd_string = "echo 1 > /sys/class/gpio/gpio{}/value".format(self.power_pin)
		#print(shell_cmd_string)
		os.system(shell_cmd_string)
		time.sleep(1)
		#power up
		shell_cmd_string = "echo 0 > /sys/class/gpio/gpio{}/value".format(self.power_pin)
		#print(shell_cmd_string)
		os.system(shell_cmd_string)
		time.sleep(1)
		shell_cmd_string = "echo 1 > /sys/class/gpio/gpio{}/value".format(self.power_pin)
		#print(shell_cmd_string)
		os.system(shell_cmd_string)
		time.sleep(1)
		shell_cmd_string = "echo 0 > /sys/class/gpio/gpio{}/value".format(self.power_pin)
		#print(shell_cmd_string)
		os.system(shell_cmd_string)
		time.sleep(1)

		self.exit_signal = int(config.config("/root/config.ini").get("SIGNAL", "EXITFLAG"))
		self.serial_ok_sig = int(config.config("/root/config.ini").get("SIGNAL", "GSMSERIALOK"))
		self.gsm_sim_not_inserted_sig = int(config.config("/root/config.ini").get("SIGNAL", "GSMSIMNOTINSERTED"))
		self.gsm_sim_module_error_sig = int(config.config("/root/config.ini").get("SIGNAL", "GSMSIMMODULEERROR"))
		signal.signal(self.exit_signal, self.exit_handler)
		self.zywlstart_pid = os.popen("ps -ef | grep zywlstart | grep -v grep | awk -F\" \" '{print $2}'").read().split('\n')[0]
		if len(self.zywlstart_pid) == 0:
			print("not find zywlstart.sh thread!")
			return False

		self.zywlstart_pid = int(self.zywlstart_pid)
		return True

	def exit_handler(self, signum, frame):
		print("receive exit signal!")
		self.exit_flag = True
		pass

	def soft_reset_gsm_module(self):
		atcmd="AT+CFUN=0\r"
		self.uart.write(bytes(atcmd.encode('utf-8')))
		bmsg = self.uart.read(32)
		time.sleep(1)
		atcmd="AT+CFUN=1\r"
		self.uart.write(bytes(atcmd.encode('utf-8')))
		bmsg = self.uart.read(32)
		time.sleep(1)

	def check_thread(self):
		errcount = 0
		self.soft_reset_gsm_module()
		while True:
			try:
				if self.exit_flag == True:
					exit(1)

				if errcount >= 5:
					errcount = 0
					self.soft_reset_gsm_module()
				
				if self.sim_module_error == 20:
					self.sim_module_error=0
					os.kill(self.zywlstart_pid, self.gsm_sim_module_error_sig)
				
				self.uart.write(bytes("AT\r".encode('utf-8')))
				bmsg = self.uart.read(32)
				if len(bmsg) == 0:
					self.sim_module_error += 1
					time.sleep(3)
					continue
				self.sim_module_error = 0
				print("AT:{}".format(bmsg))
				if "ERROR" in str(bmsg, encoding='utf-8'):
					time.sleep(1)
					errcount += 1
					continue
				
				atcmd="AT+CMEE=2\r"
				self.uart.write(bytes(atcmd.encode('utf-8')))
				bmsg = self.uart.read(128)
				print("AT+CMEE=2:{}".format(bmsg))
				if "NOT INSERTED" in str(bmsg, encoding='utf-8'):
					os.kill(self.zywlstart_pid, self.gsm_sim_not_inserted_sig)
					break

				atcmd="AT+CPIN?\r"
				self.uart.write(bytes(atcmd.encode('utf-8')))
				bmsg = self.uart.read(128)
				print("AT+CPIN?:{}".format(bmsg))

				cpinresp = str(bmsg, encoding='utf-8')
				if "READY" in cpinresp:
					errcount = 0
					atcmd="AT+COPS?\r"
					self.uart.write(bytes(atcmd.encode('utf-8')))
					bmsg = self.uart.read(128)
					print(bmsg)
					strmsg=str(bmsg, encoding='utf-8')
					if "CHN-UNICOM" in strmsg:
						print("this is a unicom card")
						shutil.copy("/etc/ppp/unicom/myppp-chat-connect", "/etc/ppp/peers/")
						os.kill(self.zywlstart_pid, self.serial_ok_sig)
					elif "CHINA MOBILE" in strmsg:
						print("this is a mobile card")
						shutil.copy("/etc/ppp/mobile/myppp-chat-connect", "/etc/ppp/peers/")
						os.kill(self.zywlstart_pid, self.serial_ok_sig)
					else:
						print("i don't know!")
						errcount += 1
				elif "SIM not inserted" in cpinresp:
					os.kill(self.zywlstart_pid, self.gsm_sim_not_inserted_sig)
					pass
				else:
					errcount += 1

				time.sleep(2)
			except Exception as e:
				print("check_ttys2isok exception:{}".format(e))
		pass

	def start_thread(self):
		t = threading.Thread(target = self.check_thread)
		t.setDaemon(False)
		t.start()

'''
atcmd = "AT+CSQ\r"
s.write(bytes(atcmd.encode('utf-8')))
bytemsg=s.read(128)
print(bytemsg)

s.write(bytes("AT+CPBS=\"ON\"\r".encode('utf-8')))
msg=s.read(128)
if "ERROR" in str(msg, encoding='utf-8'):
print("cpbs error")
exit(1)

atcmd="AT+CPBW=1,\"{}\"\r".format(test_phonenumber)
s.write(bytes(atcmd.encode('utf-8')))
msg=s.read(128)
if "ERROR" in str(msg, encoding='utf-8'):
print("cpbw error")
exit(1)

s.write(bytes("AT+CNUM\r".encode('utf-8')))
msg=s.read(128)
if "ERROR" in str(msg, encoding='utf-8'):
print("not find vaild sim card")
exit(1)

if "18642224555" not in str(msg, encoding='utf-8'):
print("sim card is not ok!")
exit(1)
'''

if __name__ == "__main__":
	s = check_ttys2isok()
	if s.open_serial() == True:
		s.start_thread()
