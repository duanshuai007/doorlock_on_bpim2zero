import threading
from threading import Timer
import time
import queue

t = None
m = None

class test():
	def task_01(self):
		try:
			self.q = queue.Queue(2)
			print("hello world")
			while True:
				try:
					msg = self.q.get(timeout=2)
					print(msg)
				except queue.Empty:
					print("queue empty")
					break
				except Exception as e:
					print("error:{}".format(e))
		except Exception as e:
			print("test:{}".format(e))

	def monitor(self):
		try:
			print("timer arrver")
			if self.t.isAlive() == True:
				print("join")
				self.t.join()
			self.t = threading.Thread(target=self.task_01)
			self.t.setDaemon(True)
			self.t.run()
			self.m = Timer(1, self.monitor)
			self.m.setDaemon(True)
			self.m.start()
		except Exception as e:
			print("test:{}".format(e))

	def timer_start(self):
		self.m = Timer(1, self.monitor)
		self.m.setDaemon(True)
		self.m.start()

	def start_thread(self):
		self.t = threading.Thread(target=self.task_01)
		self.t.setDaemon(True)
		self.t.start()

tt = test()
tt.start_thread()
tt.timer_start()

while True:
	print("dsadsadsadsa")
	time.sleep(1)
