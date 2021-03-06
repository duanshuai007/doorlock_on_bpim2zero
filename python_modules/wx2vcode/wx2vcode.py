#!/usr/bin/env python3 
#-*- coding:utf-8 -*-


import os
import sys
import json
from urllib import request, parse
from tempfile import TemporaryFile
import requests
import time

import LoggingQueue
import checkfiletype as check

#获取微信接口的二维码文件
class wx_2vcode():

	wx_token_url		= "https://api.weixin.qq.com/cgi-bin/token"
	wx_2vcode_url		= "https://api.weixin.qq.com/wxa/getwxacodeunlimit"
	server_token_url	= 

	message = {
		"scene" : "n=1",
		"page" : "",
		"width" : 280,
	}

	token_paramters = {
		"device_sn" : "",
	}
	
	def __init__(self, device_sn):
		self.logger = LoggingQueue.LoggingProducer().getlogger()
		self.token_paramters["device_sn"] = device_sn

#	def __get_accesstoken(self, url:str, msg:dict):
#		try:
#			url_values = parse.urlencode(msg)
#			fullurl = "{}?{}".format(url, url_values)
#			with request.urlopen(fullurl) as resp:
#				page = resp.read()
#				msg = str(page, encoding="utf-8")
#				msgdict = json.loads(msg)
#				if "access_token" in msgdict.keys():
#					access_token = msgdict["access_token"]
#					expires_in = msgdict["expires_in"]
#					return access_token
#				else:
#					errcode = msgdict["errcode"]
#					errmsg = msgdict["errmsg"]
#					self.logger.error("__get_accesstoken {} {}".format(errcode, errmsg))
#					return None
#		except Exception as e:
#			self.logger.error("__get_accesstoken error:{}".format(e))
#			return None
#	
#	
#	def __get_ex_2vcode(self, url:str, msg:dict, token:str)->str:
#		filepath="/tmp/wx2vcode.jpg"
#		try:
#			jsonmsg = json.dumps(msg)
#			jsonstr = str(jsonmsg)
#			#jsonbyte = bytes(jsonstr, encoding="utf-8")
#			full_url = "{}?access_token={}".format(url, token)
#			req = request.Request(full_url, bytes(jsonstr, encoding="utf-8"))
#			with request.urlopen(req) as resp:
#				page = resp.read()
#				if len(page) < 300:
#					respjson = json.loads(str(page, encoding="utf-8"))
#					if "errcode" in respjson.keys():
#						if respjson["errcode"] == 42001 or respjson["errcode"] == 40001:	#token过期
#							self.logger.warn("__get_ex_2vcode token guoqi")
#							self.wx_accesstoken = self.__get_accesstoken(self.wx_token_url, self.get_token_msg)
#							return "retry"
#							#self.logger.error("get wx2vcode failed,{}".format(page))
#					return None
#				else:
#					fd = open(filepath, 'wb+')
#					fd.write(page)
#					fd.close()
#					r = check.get_filetype(filepath)
#					if r is None:
#						self.logger.error("get weixin 2vcode failed!{}".format(page))
#						return None
#					return filepath
#		except Exception as e:
#			self.logger.error("get wx2vcode failed,{}".format(e))
#			return None
	
	#从正源物联服务器获取微信接口的token
	def __get_token_from_server(self, url:str, paramters:dict):
		try:
			req = requests.post(url, params=paramters)
			data = json.loads(req.text)
			if data['status'] == 0:
				return data['data']
			else:
				self.logger.error("get server token error:{}".format(data))
			return None
		except Exception as e:
			self.logger.error("get server token except error:{}".format(e))
			return None
	
	def __get_ex_2vcode_byservertoken(self, url:str, msg:dict, token:str)->str:
		filepath="/tmp/wx2vcode.jpg"
		try:
			jsonmsg = json.dumps(msg)
			jsonstr = str(jsonmsg)
			full_url = "{}?access_token={}".format(url, token)
			#self.logger.info("fullurl={}".format(full_url))
			#self.logger.info("body={}".format(jsonstr))
			req = request.Request(full_url, bytes(jsonstr, encoding="utf-8"))
			with request.urlopen(req) as resp:
				page = resp.read()
				if len(page) < 300:
					respjson = json.loads(str(page, encoding="utf-8"))
					self.logger.warn("get wx2vcode failed:{} {}".format(page, token))
					filepath = None
				else:
					with open(filepath, 'wb+') as f:
						f.write(page)
					r = check.get_filetype(filepath)
					if r is None:
						self.logger.error("get weixin 2vcode failed!{}".format(page))
						filepath =  None
			return filepath
		except Exception as e:
			self.logger.error("get wx2vcode by server token failed,{}".format(e))
			return None

	def get_2vcode(self, msgdict:dict):

		self.message["page"] = msgdict["page"]
		if len(msgdict["scene"]) != 0:
			#self.message["scene"] = msgdict["scene"]
			self.message["scene"] = "{}-{}".format(self.token_paramters["device_sn"], msgdict["scene"])
		'''
		ret = self.__get_ex_2vcode(self.wx_2vcode_url, self.message, self.wx_accesstoken)
		if ret == "retry":
			ret = self.__get_ex_2vcode(self.wx_2vcode_url, self.message, self.wx_accesstoken)
		'''
		for i in range(10):
			accesstoken = self.__get_token_from_server(self.server_token_url, self.token_paramters)
			if accesstoken is not None:
				ret = self.__get_ex_2vcode_byservertoken(self.wx_2vcode_url, self.message, accesstoken)
				if ret is not None:
					return ret
			time.sleep(0.5)
		return None

if __name__ == "__main__":
	ss = wx_2vcode("dsadsadas")
	ret = ss.get_token()
	print(ret)
