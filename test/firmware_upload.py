#!/usr/bin/env python3
#-*- coding:utf-8 -*-

import os
import sys
import requests
import json

class uopload_firmware():

	url = "https://acstest.iotwonderful.cn/upgrade/upload"
	filename = None

	def set_upload_file(self, filename:str):
		if not os.path.exists(filename):
			print("file:{} is not exists".format(filename))
			return
		self.filename = filename
	
	def upload(self):
		with open(self.filename, 'rb') as f:
			msg = f.read()		
		files = {"file":msg}
		req = requests.post(self.url, files=files)
		text = json.loads(req.text)
		print(text["status"])
		print(text["message"].encode("utf-8"))
		print(text["data"])

if __name__ == "__main__":
	if len(sys.argv) < 2:
		print("input firmware path")
		exit(1)
	firmware_path = sys.argv[1]
	u = uopload_firmware()
	u.set_upload_file(firmware_path)
	u.upload()
