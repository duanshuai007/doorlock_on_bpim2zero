#!/usr/bin/env python3
#-*- coding:utf-8 -*-

import json
import requests

#https://api.weixin.qq.com/sns/jscode2session?appid=APPID&secret=SECRET&js_code=JSCODE&grant_type=authorization_code

def get_token():
	url="https://api.weixin.qq.com/sns/jscode2session"
	fullurl = "{}?appid={}&secret={}&js_code={}&grant_type={}".format(url, "wx187e04e3d62e8aa5", "afe0d2d7203eeea19acef3fac07bb6db", "021SXc1003v9IK1wwx100yrvrY3SXc1s","authorization_code")
	req = requests.get(fullurl)
	data = json.loads(req.text)
	print(data)

if __name__ == "__main__":
	token = get_token()
