#!/usr/bin/env python3
#-*- coding:utf-8 -*-

import json
import requests

url="https://acstest.iotwonderful.cn/api/access/token"
msg = {
	"device_sn":"02421a71c57b"
}

def get_token():
	url="https://acstest.iotwonderful.cn/api/access/token"
	values = {
		"device_sn":"02421a71c57b"
	}
	req = requests.post(url, params=values)
	data = json.loads(req.text)
	if data['status'] == 0:
		return data['data']
	return None

def get_2vcode(token:str):
	message = { 
		"scene" : "0242074b7d2b-1597304702",
		"page" : "pages/index/index",
		"width" : 280,
	}
	url="https://api.weixin.qq.com/wxa/getwxacodeunlimit"
	url="{}?access_token={}3".format(url, token)
	print(url)
	jsonstr = str(json.dumps(message))
	bmsg = bytes(jsonstr, encoding='utf-8')
	req = requests.post(url, data=bmsg)
	print(req)
	print(req.text)
	print("status code={}".format(req.status_code))
	print("reason={}".format(req.reason))

if __name__ == "__main__":
	token = get_token()
	print(token)
	get_2vcode(token)
