#!/usr/bin/env python3
#-*- coding:utf-8 -*-

import json
import requests

def get_token():
	url=
	values = {
		"device_sn":
	}
	req = requests.post(url, params=values)
	data = json.loads(req.text)
	print(data)
	if data['status'] == 0:
		return data['data']
	return None

def get_2vcode(token:str):
	message = { 
		"scene" : "02421a71c57b-1601005210",
		"page" : "pages/index/index",
		"width" : 280,
	}
	url="https://api.weixin.qq.com/wxa/getwxacodeunlimit"
	url="{}?access_token={}".format(url, token)
	print(url)
	jsonstr = str(json.dumps(message))
	bmsg = bytes(jsonstr, encoding='utf-8')
	req = requests.post(url, data=bmsg)
	print(req)
	#print(req.text)
	if len(req.text) < 3000:
		print(req.text)
	print("status code={}".format(req.status_code))
	#print("reason={}".format(req.reason))
	with open("wx2vcode.jpg", 'wb') as f:
		f.write(req.content)

if __name__ == "__main__":
	token = get_token()
	print(token)
	get_2vcode(token)
