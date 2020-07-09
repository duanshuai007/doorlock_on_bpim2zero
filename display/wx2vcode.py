#!/usr/bin/env python3 
#-*- coding:utf-8 -*-


import os
import sys
import json
from urllib import request, parse
import config
import LoggingQueue
import display.checkfiletype as check

class wx_2vcode():

	wx_token_url = "https://api.weixin.qq.com/cgi-bin/token"
	wx_2vcode_url="https://api.weixin.qq.com/wxa/getwxacodeunlimit"
	server_token_url = "https://acstest.iotwonderful.cn/access/token"

	message = {
		"scene" : "n=1",
		"page" : "",
		"width" : 280,
	}
	
	get_token_msg = {
		"grant_type" : "client_credential",
		"appid" : "wxd459af37673abbd6",
		"secret" : "ee3b7bc1a4eed49b99e574794acaf51c",
	}

	wx_accesstoken = None

	def __init__(self):
		c = config.config()
		self.wx_token_url = c.get("WEIXIN", "TOKEN_URL")
		self.wx_2vcode_url = c.get("WEIXIN", "2VCODE_URL")
		self.wx_appid = c.get("WEIXIN", "APPID")
		self.wx_secret = c.get("WEIXIN", "SECRET")
		self.logger = LoggingQueue.LoggingProducer().getlogger()

	def __get_accesstoken(self, url:str, msg:dict):
		try:
			url_values = parse.urlencode(msg)
			fullurl = "{}?{}".format(url, url_values)
			with request.urlopen(fullurl) as resp:
				page = resp.read()
				msg = str(page, encoding="utf-8")
				msgdict = json.loads(msg)
				if "access_token" in msgdict.keys():
					access_token = msgdict["access_token"]
					expires_in = msgdict["expires_in"]
					return access_token
				else:
					errcode = msgdict["errcode"]
					errmsg = msgdict["errmsg"]
					self.logger.error("__get_accesstoken {} {}".format(errcode, errmsg))
					return None
		except Exception as e:
			self.logger.error("__get_accesstoken error:{}".format(e))
			return None

	def __get_ex_2vcode(self, url:str, msg:dict, token:str)->str:
		filepath="/tmp/wx2vcode.jpg"
		try:
			jsonmsg = json.dumps(msg)
			jsonstr = str(jsonmsg)
			#jsonbyte = bytes(jsonstr, encoding="utf-8")
			full_url = "{}?access_token={}".format(url, token)
			req = request.Request(full_url, bytes(jsonstr, encoding="utf-8"))
			with request.urlopen(req) as resp:
				page = resp.read()
				if len(page) < 300:
					respjson = json.loads(str(page, encoding="utf-8"))
					if "errcode" in respjson.keys():
						if respjson["errcode"] == 42001 or respjson["errcode"] == 40001:	#token过期
							self.logger.warn("__get_ex_2vcode token guoqi")
							self.wx_accesstoken = self.__get_accesstoken(self.wx_token_url, self.get_token_msg)
							return "retry"
							#self.logger.error("get wx2vcode failed,{}".format(page))
					return None
				else:
					fd = open(filepath, 'wb+')
					fd.write(page)
					fd.close()
					r = check.get_filetype(filepath)
					if r is None:
						self.logger.error("get weixin 2vcode failed!{}".format(page))
						return None
					return filepath
		except Exception as e:
			self.logger.error("get wx2vcode failed,{}".format(e))
			return None

	def __get_token_from_server(self, url:str):
		try:
			ret = None
			with request.urlopen(url) as resp:
				page = resp.read()
				if page is not None and page != False and page != "false" and page != "False":
					ret = str(page, encoding="utf-8")
			return ret
		except Exception as e:
			self.logger.error("__get_token_from_server error:{}".format(e))
			return None
	
	def __get_ex_2vcode_byservertoken(self, url:str, msg:dict, token:str)->str:
		filepath="/tmp/wx2vcode.jpg"
		try:
			jsonmsg = json.dumps(msg)
			jsonstr = str(jsonmsg)
			full_url = "{}?access_token={}".format(url, token)
			#self.logger.info("fullurl={}".format(full_url))
			req = request.Request(full_url, bytes(jsonstr, encoding="utf-8"))
			with request.urlopen(req) as resp:
				page = resp.read()
				if len(page) < 300:
					respjson = json.loads(str(page, encoding="utf-8"))
					self.logger.warn("__get_ex_2vcode_byservertoken error:{}".format(page))
					filepath = None
					if "errcode" in respjson.keys():
						if respjson["errcode"] == 42001 or respjson["errcode"] == 40001:    #token过期
							#self.logger.warn("_get_ex_2vcode by server token guoqi")
							self.wx_accesstoken = self.__get_token_from_server(self.server_token_url)
							filepath = "retry"
				else:
					fd = open(filepath, 'wb+')
					fd.write(page)
					fd.close()
					r = check.get_filetype(filepath)
					if r is None:
						self.logger.error("get weixin 2vcode failed!{}".format(page))
						filepath =  None
			return filepath
		except Exception as e:
			self.logger.error("get wx2vcode by server token failed,{}".format(e))
			return None

	def get_2vcode(self, msgdict:dict):
		if self.wx_accesstoken is None:
			#self.wx_accesstoken = self.__get_accesstoken(self.wx_token_url, self.get_token_msg)
			self.wx_accesstoken = self.__get_token_from_server(self.server_token_url)
			if self.wx_accesstoken is None:
				self.logger.error("get 2vcode token is None")
				return None
		self.message["page"] = msgdict["page"]
		if len(msgdict["scene"]) != 0:
			self.message["scene"] = msgdict["scene"]
		'''
		ret = self.__get_ex_2vcode(self.wx_2vcode_url, self.message, self.wx_accesstoken)
		if ret == "retry":
			ret = self.__get_ex_2vcode(self.wx_2vcode_url, self.message, self.wx_accesstoken)
		'''
		ret = self.__get_ex_2vcode_byservertoken(self.wx_2vcode_url, self.message, self.wx_accesstoken)
		if ret == "retry":
			ret = self.__get_ex_2vcode_byservertoken(self.wx_2vcode_url, self.message, self.wx_accesstoken)
		if ret == "retry":
			return None
		else:
			return ret

if __name__ == "__main__":
	ss = wx_2vcode()
	#ret = ss.get_2vcode()
	ret = ss.get_token()
	print(ret)
