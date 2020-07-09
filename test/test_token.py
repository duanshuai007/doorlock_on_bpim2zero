#!/usr/bin/env python3
#-*- coding:utf-8 -*-

import json
from urllib import request, parse

url="https://acstest.iotwonderful.cn/access/token"

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
	print(get_token(url))
	
