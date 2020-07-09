#!/usr/bin/env python3
#-*- coding:utf-8 -*-

import os
import sys 
import configparser

class config():
	rootdir = ''
	config = None

	def __init__(self):
		self.rootdir = os.path.dirname(os.path.abspath(sys.argv[0]))
		self.config = configparser.ConfigParser()
		self.config.read(self.rootdir + "/config.ini")
		pass

	def get(self:object, string:str, substring:str)->str:
		try:
			ret = self.config[string][substring]
			if substring in ["CAFILE", "LOGFILE"]:
				ret = self.rootdir + '/' + ret 
			return ret 
		except Exception as e:
			#self.logger.error("Config get error:{} {} {}",format(string, substring, e))
			print(e)
		return ''

	def set(self:object, string:str, substring:str, value:str)->bool:
		try:
			self.config.set(string, substring, value)
			with open(self.rootdir + "/config.ini", 'w') as f:
				self.config.write(f)
			return True
		except Exception as e:
			print("Config set error:{}".format(e))
			return False

if __name__ == '__main__':
	c = config()
	r = c.get("MQTT", "USER")
	print(r)
	r = c.set("DOORLOCK", "OPEN_TIME", "20")
	print(r)
	pass
