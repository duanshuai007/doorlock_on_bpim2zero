import urllib.request 
import urllib.parse
import json
import hashlib

def __get_updatefirmware_token():
	try:
		#post
		token_url = "https://acstest.iotwonderful.cn/api/upgrade/login"
		message = { 
			"user" : "xinchao@iotwonderful.com",
			"password" : "123456"
		}   
		data = urllib.parse.urlencode(message).encode()
		req = urllib.request.Request(token_url, data=data)

		with urllib.request.urlopen(req) as resp:
			page = resp.read()
			msgdict = json.loads(str(page, encoding="utf-8"))
			print(msgdict)
			if msgdict is not None:
				return msgdict["token"]
		return None
	except Exception as e:
		print(e)
		return None

def __down_firmware(token:str):
	try:
		#url = "https://acstest.iotwonderful.cn/api/upgrade/download?file_name=upgrade/7d0f4085.png"
		url = "https://acstest.iotwonderful.cn/api/upgrade/download?file_name=upgrade/6b863767.gz"
		fullurl = "{}&token={}".format(url, token)
		print(fullurl)
		m = hashlib.md5()
		size = 0
		with urllib.request.urlopen(fullurl) as resp:
			page = 's'
			while page != b'':
				page = resp.read(1024)
				#m = hashlib.md5(page)
				#print(page)
				m.update(page)
				size += len(page)
		print(m.hexdigest())
		print("size = {}".format(size))
	except Exception as e:
		print(e)
	
def __down_2(token):
	try:
		#url = "https://acstest.iotwonderful.cn/api/upgrade/download?file_name=upgrade/7d0f4085.png"
		url = "https://acstest.iotwonderful.cn/api/upgrade/download?file_name=upgrade/6b863767.gz"
		fullurl = "{}&token={}".format(url, token)
		#print(fullurl)
		r = urllib.request.urlretrieve(fullurl, "./test.png")
		#print(r)
		m2 = hashlib.md5()
		with open("./test.png", 'rb') as f:
			msg = 's'
			while msg != b'':
				msg = f.read(1024)
				#print(msg)
				m2.update(msg)
		print(m2.hexdigest())
	except Exception as e:
		print(e)

if __name__ == "__main__":
	token = __get_updatefirmware_token()
	if token is not None:
		__down_firmware(token)
		#__down_2(token)

