#!/usr/bin/env python2
#-*- coding:utf-8 -*-

import cv2
import numpy as np
import sys
import os
import spilcd

def test_opencv(filename):
	if not os.path.exists(filename):
		print("file not exists!")
		exit(1)
	
	flag = False	#点组成值的标志位，两个点组成一个值
	value = 0	#值
	imgbuffer = []
	img = cv2.imread(filename)
	img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
	h,w = img.shape
	print("img col={},row={}".format(w, h))
	resizeimg = cv2.resize(img, ((162,160)), 162/430, 160/430, cv2.INTER_LINEAR)
	cv2.imwrite("resizeimg.jpg", resizeimg)
	for row in range(160):
		#for col in range(162, 0):
		col = 162
		while col > 0:
			col -= 1
			pv = resizeimg[row, col]
			if flag is True:
				flag = False
				value <<= 4
				if pv > 180:
					value |= 0xf		
				imgbuffer.append(pv)
			else:
				value = 0;
				flag = True
				if pv > 180:
					value |= 0xf
	spilcd.show(imgbuffer)

if __name__ == "__main__":
	
	if len(sys.argv) < 2:
		print("please input image path")
		exit(1)
	print("file name:{}".format(sys.argv[1]))	
	test_opencv(sys.argv[1])
