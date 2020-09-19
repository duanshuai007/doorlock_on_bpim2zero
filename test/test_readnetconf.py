#!/usr/bin/env python3
#-*- coding:utf-8 -*-

def test_func():
	with open("../net.conf", 'r') as f:
		while True:
			line = f.readline()
			if len(line) == 0:
				break
			else:
				line = line.split('\n')[0]
				if line is not None:
					if line.startswith("ssid="):
						print(line.split("=")[1])
					if line.startswith("psk="):
						print(line.split("=")[1])

if __name__ == "__main__":
	test_func()
