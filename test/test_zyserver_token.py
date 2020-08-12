#!/usr/bin/env python3
#-*- coding:utf-8 -*-

import json
from urllib import request, parse

url="https://acstest.iotwonderful.cn/access/token"
msg = {
	"device_sn":"02421a71c57b"
}

def get_token_from_server(url:str):
	try:
		global msg
		jsonmsg = json.dumps(msg)
		jsonstr = str(jsonmsg)
		print("body={}".format(jsonstr))
		req = request.Request(url, bytes(jsonstr, encoding="utf-8"))
		with request.urlopen(req) as resp:
			page = resp.read()
			print(page)
			return ret
	except Exception as e:
		print(e)

def get_token(url:str):
	try:
		print(url)
		with request.urlopen(url) as resp:
			page = resp.read()
			if page is not None and page != False and page != "false" and page != "False":
				return str(page, encoding="utf-8")
		pass
	except Exception as e:
		print("error:{}".format(e))
		pass

if __name__ == "__main__":
	#print(get_token(url))
	get_token_from_server(url)
