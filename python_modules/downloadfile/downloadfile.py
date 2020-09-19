#!/usr/bin/env python3
#-*- coding:utf-8 -*-

import urllib.request 
import urllib.parse
import os
import hashlib
import json

import LoggingQueue
import message_struct as ms
import checkfiletype as check
url = "https://timgsa.baidu.com/timg?image&quality=80&size=b9999_10000&sec=1591866200525&di=e880ae3dc16c07985a292a24f3842a1d&imgtype=0&src=http%3A%2F%2Ft9.baidu.com%2Fit%2Fu%3D770196171%2C1212335633%26fm%3D1931"

log = LoggingQueue.LoggingProducer().getlogger()

filesize = 0

def callback(a, b, c):
	global filesize
	filesize = c

def download(url:str, filename:str)->int:
	try:
		global log
		global filesize
		if url is not None:
			r = urllib.request.urlretrieve(url, filename, callback)
			r = check.get_filetype(filename)
			if r is None:
				log.error("download file type error.")
				return 1
			size = os.path.getsize(filename)
			if size == filesize:
				return 0
			else:
				log.error("download file size({}) error.".format(size))
				return 2
		else:
			return 3
	except Exception as e:
		log.error("download failed, url:{} filename:{} error:{}".format(url, filename, e))
		return 4

def __get_updatefirmware_token():
	try:
		#post
		#token_url = "https://acstest.iotwonderful.cn/api/upgrade/login"
		token_url = ms.UPGRADE_TOKEN_URL
		message = { 
			#"user" : "xinchao@iotwonderful.com",
			#"password" : "123456"
			"user" : ms.UPGRADE_USERNAME,
			"password" : ms.UPGRADE_PASSWORD
		}   
		data = urllib.parse.urlencode(message).encode()
		req = urllib.request.Request(token_url, data=data)

		with urllib.request.urlopen(req) as resp:
			page = resp.read()
			msgdict = json.loads(str(page, encoding="utf-8"))
			if msgdict is not None:
				if msgdict["status"] == 0:
					return msgdict["token"]
		return None
	except Exception as e:
		print(e)
		return None

def download_firmware(url:str, md5:str, filename:str)->bool:
	try:
		global log
		if url is not None:
			token = __get_updatefirmware_token()
			if token is not None:
				full = "{}&token={}".format(url, token)
				
				if not os.path.exists(filename):
					r = os.path.split(filename)
					if not os.path.exists(r[0]):
						os.makedirs(r[0])

				urllib.request.urlretrieve(full, filename)
				
				m = hashlib.md5()
				with open(filename, 'rb') as filehandler:
					msg = '1'
					while msg != b'':
						msg = filehandler.read(1024)
						m.update(msg)
				md5value = m.hexdigest()
				if md5value != md5:
					log.error("download {} md5 error.".format(url))
					return False
				
				return True
		return False
	except Exception as e:
		log.error("download failed, url:{} filename:{} error:{}".format(url, filename, e))
		return False

if __name__ == "__main__":
	r = download(url, "test.jpg")
	print(r)
