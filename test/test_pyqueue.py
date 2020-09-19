#!/bin/bash

import queue
import threading
import time
from threading import Timer
class test_queue():

	def ttt(self):
		while True:
			q = self.consumer.get()
			print(q)

	def www(self):
		i = 0
		while True:
			self.consumer.put("hello world:{}".format(i))
			time.sleep(1)
			i=i+1

	def run(self):
		self.consumer = queue.Queue(32)
		t = threading.Thread(target = self.ttt)	
		t.setDaemon(True)
		t.start()
		
		w = threading.Thread(target = self.www)
		w.setDaemon(True)
		w.start()
	
def testTask():
	print(time.time())
	print("testTask")

def testTask1():
	print(time.time())
	print("testTask1")

def testTimer():
	s = Timer(3, testTask)
	s.setDaemon(False)
	s.start()
	s1 = Timer(1, testTask1)
	s1.setDaemon(False)
	s1.start()

def test_whileTimer():
	while True:
		s = Timer(3, testTask)
		s.setDaemon(False)
		s.start()
		time.sleep(1)
		if s.isAlive() == True:
			print("timer alive")
		#s.cancel()
		print("join")
		s.join()
		if s.isAlive() == False:
			print("timer dead")
	
		print("dsadsadsadas")

if __name__ == "__main__":
	t = test_queue()
	t.run()
	while True:
		time.sleep(1)
		print("allllllllllllllllllllll")
#	testTimer()
#test_whileTimer()
