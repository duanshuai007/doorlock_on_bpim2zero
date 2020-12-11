#!/usr/bin/env python3 
#-*- coding:utf-8 -*-

import os
import sys 
import json
from urllib import request, parse
from tempfile import TemporaryFile
import requests
import threading
import time
import logging

wx_token_url = "https://api.weixin.qq.com/cgi-bin/token"
get_token_msg = {
 "grant_type" : "client_credential",
  "appid" : 
  "secret" : 
}

def initLogging(logFilename):
	logging.basicConfig(
			level = logging.INFO,
			format ='%(asctime)s-%(levelname)s:%(message)s',
			datefmt = '%y-%m-%d %H:%M:%S',
			filename = logFilename,
			filemode = 'a')
						   
						   
def get_accesstoken(url:str, msg:dict):
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
#获取微信接口的二维码文件
class wx_2vcode():

	wx_2vcode_url="https://api.weixin.qq.com/wxa/getwxacodeunlimit"
	server_token_url = 

	message = { 
		"scene" : "n=1",
		"page" : "", 
		"width" : 280,
	}   

	token_paramters = { 
		"device_sn" : "", 
	}   
	
	def __init__(self, device_sn):
		self.logger = logging.getLogger("wx2vcode")
		self.logger.setLevel(logging.DEBUG)
		self.token_paramters["device_sn"] = device_sn
		self.device_sn = device_sn
		self.filepath="./{}/wx2vcode.jpg".format(self.device_sn)
		if not os.path.exists(self.filepath):
			r = os.path.split(self.filepath)
			self.logger.info("path:{}".format(r))
			if not os.path.exists(r[0]):
				os.makedirs(r[0])
	#从正源物联服务器获取微信接口的token
	def __get_token_from_server(self, url:str, paramters:dict):
		try:
			req = requests.post(url, params=paramters)
			data = json.loads(req.text)
			if data['status'] == 0:
				return data['data']
			else:
				self.logger.error("{}:get token error:{}".format(self.device_sn, data))
				return None
		except Exception as e:
			self.logger.error("{}:get token except error:{}".format(self.device_sn, e))
			return None

	def __get_ex_2vcode_byservertoken(self, url:str, msg:dict, token:str)->str:
		try:
			jsonmsg = json.dumps(msg)
			jsonstr = str(jsonmsg)
			full_url = "{}?access_token={}".format(url, token)
#self.logger.info("fullurl={}".format(full_url))
#			self.logger.info("body={}".format(jsonstr))
			req = request.Request(full_url, bytes(jsonstr, encoding="utf-8"))
			with request.urlopen(req) as resp:
				page = resp.read()
				if len(page) < 300:
					respjson = json.loads(str(page, encoding="utf-8"))
					self.logger.warn("{}:get servertoken error:{}".format(self.device_sn, page))
#self.logger.warn("{}: token:{}".format(self.device_sn, token))
					return None
				else:
					with open(self.filepath, 'wb+') as f:
						f.write(page)
						self.logger.info("{}:get weixin 2vcode ok!".format(self.device_sn))
			return self.filepath
		except Exception as e:
			self.logger.error("{}:get wx2vcode by server token failed,{}".format(self.device_sn,e))
			return None

	def get_2vcode(self, msgdict:dict):
		self.message["page"] = msgdict["page"]
		if len(msgdict["scene"]) != 0:
			self.message["scene"] = msgdict["scene"]
		accesstoken = self.__get_token_from_server(self.server_token_url, self.token_paramters)
		if accesstoken is not None:
			ret = self.__get_ex_2vcode_byservertoken(self.wx_2vcode_url, self.message, accesstoken)
			return ret
		return None

	def get_2vcode_already_have_token(self, msgdict:dict, token:str):
		self.message["page"] = msgdict["page"]
		if len(msgdict["scene"]) != 0:
			self.message["scene"] = msgdict["scene"]
		ret = self.__get_ex_2vcode_byservertoken(self.wx_2vcode_url, self.message, token)
		return ret

def pool_get_2vcode(wx_handler:object, token:str):
	logging.info("pool_get_2vcode:device sn = {}".format(wx_handler.device_sn))
	msg = {
		"page" : "pages/index/index",
		"scene" : "",
	}

	while True:
		msg["scene"] = "{}-{}".format(wx_handler.device_sn, int(time.time()))
		wx_handler.get_2vcode_already_have_token(msg, token)
#time.sleep(1)

if __name__ == "__main__":
	initLogging("./test_wx2vcode.log")
	token = get_accesstoken(wx_token_url, get_token_msg)
	if token is None:
		logging.error("get token error")
		exit(1)

	w1 = wx_2vcode("02420877c9cc")
	s1 = threading.Thread(target = pool_get_2vcode, args=[w1, token])
	s1.setDaemon(False)

	w2 = wx_2vcode("0242fe007c52")
	s2 = threading.Thread(target = pool_get_2vcode, args=[w2, token])
	s2.setDaemon(False)
	
	w3 = wx_2vcode("02421a71c57b")
	s3 = threading.Thread(target = pool_get_2vcode, args=[w3, token])
	s3.setDaemon(False)

	s1.start()
	s2.start()
	s3.start()

