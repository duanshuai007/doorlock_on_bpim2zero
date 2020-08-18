#!/usr/bin/env python3
#-*- coding:utf-8 -*-

import os
import sys
import config
import signal
import queue
import time
import threading

import watchdog

class feed_dog():

	curr = 0
	last = 0

	def __init__(self, sig_feed, sig_stop):
		signal.signal(sig_feed, self.signal_feed_callback)
		signal.signal(sig_stop, self.signal_stop_callback)
		self.r = queue.Queue(2)
		self.curr = int(time.time())
		self.last = int(time.time())
		pass

	def signal_feed_callback(self, signum, frame):
		self.r.put("f")
		pass

	def signal_stop_callback(self, signum, frame):
		self.r.put("s")
		pass

	def main_thread(self):
		watchdog.feed()
		while True:
			try:
				m = self.r.get()
				if m == "f":
					watchdog.feed()
					print("receive feed")
					pass
				elif m == "s":
					watchdog.stop()
					print("receive stop")
					break
			except Exception as e:
				print("watchdog error:{}".format(e))
		pass

	def run(self):
		t = threading.Thread(target = self.main_thread)
		t.setDaemon(False)
		t.start()

if __name__ == "__main__":
	if len(sys.argv) < 3:
		print("paramters error")
		exit(1)
	sig_feed = int(sys.argv[1])
	sig_stop = int(sys.argv[2])
	s = feed_dog(sig_feed, sig_stop)
	s.run()
