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
import select
import queue
from threading import Timer

import LoggingQueue

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
		self.inputs = [self.uart]
		self.outputs = []

		self.cmd_queue = queue.Queue(8)
		self.resp_queue = queue.Queue(8)
		self.logger = LoggingQueue.LoggingProducer().getlogger()

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

	def create_gpio_hand(self, pin:int):
		if not os.path.exists("/sys/class/gpio/gpio{}".format(pin)):
			shell_cmd_string = "echo {} > /sys/class/gpio/export".format(pin)
			os.system(shell_cmd_string)
			shell_cmd_string = "echo out > /sys/class/gpio/gpio{}/direction".format(pin)
			os.system(shell_cmd_string)
	def destory_gpio_hand(self, pin:int):
		if os.path.exists("/sys/class/gpio/gpio{}".format(pin)):
			shell_cmd_string = "echo {} > /sys/class/gpio/unexport".format(pin)
			os.system(shell_cmd_string)

	def set_pwr_key(self, val:int):
		shell_cmd_string = "echo {} > /sys/class/gpio/gpio{}/value".format(val, self.power_pin)
		os.system(shell_cmd_string)

	def exit_handler(self, signum, frame):
		print("receive exit signal!")
		self.exit_flag = True
		pass

	def hard_reset_gsm_module(self):
		self.create_gpio_hand(self.power_pin)
		#do gsm module power up	
		#power down 因为在电路上做了取反，所以对应的控制电平就是反的
		self.set_pwr_key(0)
		time.sleep(2)
		self.set_pwr_key(1)
		time.sleep(1)
		#power up
		self.set_pwr_key(0)
		time.sleep(1)
		self.set_pwr_key(1)
		time.sleep(1)
		self.set_pwr_key(0)
		time.sleep(1)
		self.destory_gpio_hand(self.power_pin)

	def soft_reset_gsm_module(self):
		print("enter soft_reset_gsm_module")
		ret = False
		errcount = 0
		while True:
			result = self.send_atcmd_and_wait_response("AT+CFUN=0\r\n", 5)
			if "+CPIN: NOT READY" in result:
				pass
			elif "OK" in result:
				print(result)
				result = self.send_atcmd_and_wait_response("AT+CFUN=1\r\n", 5)
				print(result)
				if "+CPIN: READY" in result:
					ret = True
					break
				elif "+CPIN: NOT INSERTED" in result:
					ret = False
					break
			else:
				errcount += 1
				if errcount >= 5:
					self.hard_reset_gsm_module()
					errcount = 0
			time.sleep(1)
		print("exit soft_reset_gsm_module")
		return ret

	def __deal_with_response(self, response:str):
		try:	
			if "ERROR" in response or "OK" in response:
				return True
			else:
				return False
		except Exception as e:
			print("__deal_with_response error:{}".format(e))

	def send_atcmd_and_wait_response(self, atcmd:str, wait:int):
		strmsg = ""
		try:
			print("cmd:{}".format(atcmd))
			self.uart.write(bytes(atcmd.encode('utf-8')))
			curtime = int(time.time())
			timeout = curtime + wait
			while curtime < timeout:
				curtime = int(time.time())
				bmsg = self.uart.read(1024)
				if len(bmsg) != 0:
					strmsg += str(bmsg, encoding='utf-8')
					if strmsg.endswith('\r\n'):
						ret = self.__deal_with_response(strmsg)
						if ret == True:
							break
				time.sleep(0.1)
		except Exception as e:
			print("send_atcmd_and_wait_response error:{}".format(e))
		finally:
			return strmsg

	def writecmd_and_readresponse_thread(self):
		errcount = 0
		not_register_count = 0
		card_cant_register = 0
		sim_card_not_insert = 0
		status = 0
		if self.soft_reset_gsm_module() == False:
			os.kill(self.zywlstart_pid, self.gsm_sim_not_inserted_sig)
			print("not find sim card,i will exit")
			exit(1)

		while True:
			try:
				if self.exit_flag == True:
					exit(1)

				if status == 0:	
					ret = self.send_atcmd_and_wait_response("AT\r\n", 3)
					print("response:{}".format(ret))
					if len(ret) == 0:
						errcount += 1
						if errcount >= 10:
							errcount = 0
							self.soft_reset_gsm_module()
					else:
						status = 1
				if status == 1:
					ret = self.send_atcmd_and_wait_response("AT+CMEE=2\r\n", 3)
					print("response:{}".format(ret))
					if "AT+CMEE=2" in ret:
						if "OK" in ret:
							status = 2
						else:
							self.soft_reset_gsm_module()
							status = 0
				if status == 2:
					ret = self.send_atcmd_and_wait_response("AT+CPIN?\r\n", 3)
					print("response:{}".format(ret))
					if "AT+CPIN?" in ret:
						if "+CPIN: READY" in ret:
							status = 3
						elif "+CME ERROR: SIM busy":
							time.sleep(1)
						elif "ERROR" in ret:
							if "CFUN state is 0 or 4" in ret or "SIM not inserted" in ret:
								if sim_card_not_insert == 0:
									self.soft_reset_gsm_module()
									sim_card_not_insert = 1
									status = 0
								else:
									os.kill(self.zywlstart_pid, self.gsm_sim_not_inserted_sig)
									time.sleep(2)
				if status == 3:
					ret = self.send_atcmd_and_wait_response("AT+CREG?\r\n", 3)
					if "AT+CREG?" in ret:
						if "+CREG: 0,1" in ret:
							not_register_count = 0
							status = 4
							pass
						else:
							not_register_count += 1
							if not_register_count >= 20:
								if card_cant_register == 0:
									card_cant_register = 1
									not_register_count = 0
									status = 0
									self.hard_reset_gsm_module()
								else:
									print("this card can't register")
									#send signal to zywlstart.sh
									os.kill(self.zywlstart_pid, self.gsm_sim_module_error_sig)
							time.sleep(2)
				if status == 4:
					ret = self.send_atcmd_and_wait_response("AT+COPS?\r\n", 5)
					#print("response:{}".format(ret))
					if "AT+COPS?" in ret:
						if "CHINA MOBILE" in ret:
							errcount = 0
							print("this is a china mobile card")
							shutil.copy("/etc/ppp/mobile/myppp-chat-connect", "/etc/ppp/peers/")
							os.kill(self.zywlstart_pid, self.serial_ok_sig)
						elif "CHN-UNICOM" in ret:
							errcount = 0
							print("this is a china unicom card")
							shutil.copy("/etc/ppp/unicom/myppp-chat-connect", "/etc/ppp/peers/")
							os.kill(self.zywlstart_pid, self.serial_ok_sig)
						else:
							print("sorry,i don't know what kind of card")
							errcount += 1
							if errcount >= 3:
								errcount = 0
								status = 0
								self.soft_reset_gsm_module()
					time.sleep(2)
			except Exception as e:
				print("writecmd_and_readresponse_thread error:{}".format(e))

	def start_thread(self):
		t = threading.Thread(target = self.writecmd_and_readresponse_thread)
		t.setDaemon(False)
		t.start()

if __name__ == "__main__":
	s = check_ttys2isok()
	if s.open_serial() == True:
		s.start_thread()
