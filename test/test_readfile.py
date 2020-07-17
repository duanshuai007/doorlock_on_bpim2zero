#!/usr/bin/env python3
#-*- coding:utf-8 -*-

import sys
import os

def readfile(filename:str):
	with open(filename, 'r') as f:
		#line = f.read(1024).split('\n')[0]
		line = f.read(1024)
		if line is None:
			print("read None")
		print(line)
	s = os.path.getsize(filename)
	print("size = {}".format(s))
if __name__ == '__main__':
	filename = sys.argv[1]
	readfile(filename)
