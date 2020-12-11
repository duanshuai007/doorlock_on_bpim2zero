#!/usr/bin/env python3
#-*- coding:utf-8 -*-

import json
import requests
#import binascii

url=

def get_token(url):
	values = {
		"device_sn":
	}
	req = requests.post(url, params=values)
	print(req.status_code)
	print("len={}".format(len(req.content)))
	if len(req.content) == 1762:
		count = 0
		m = ""
		for i in req.content:
			#print("{},{}".format((binascii.hexlify(bytes(i, encoding="utf-8"))), count))
			s = "{}".format(hex(i))
			if (len(s) == 3):
				s = "0{}".format(s)
			m += " " + s
			count += 1
			if count  == 20:
				count = 0
				m += "\r\n"

		print(m)

if __name__ == "__main__":
	token = get_token(url)
