import urllib.request 
import os
import LoggingQueue
import display.checkfiletype as check
url = "https://timgsa.baidu.com/timg?image&quality=80&size=b9999_10000&sec=1591866200525&di=e880ae3dc16c07985a292a24f3842a1d&imgtype=0&src=http%3A%2F%2Ft9.baidu.com%2Fit%2Fu%3D770196171%2C1212335633%26fm%3D1931"

log = LoggingQueue.LoggingProducer().getlogger()

filesize = 0

def callback(a, b, c):
	global filesize
	filesize = c

def download(url:str, filename:str)->bool:
	try:
		global log
		global filesize
		if url is not None:
			r = urllib.request.urlretrieve(url, filename, callback)
			r = check.get_filetype(filename)
			if r is None:
				log.error("download file type error.")
				return False
			size = os.path.getsize(filename)
			if size == filesize:
				return True
			else:
				log.error("download file size({}) error.".format(size))
				return False
		else:
			return False
	except Exception as e:
		log.error("download failed, url:{} filename:{} error:{}".format(url, filename, e))
		return False

if __name__ == "__main__":
	r = downfile(url, "test.jpg")
	print(r)
