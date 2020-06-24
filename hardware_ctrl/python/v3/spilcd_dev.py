#!/usr/bin/env python3
#-*- coding:utf-8 -*-

from display.hardware.spilcd_interface import spilcd_interface

class spilcd_dev():

	def __init__(self):
		self.spilcd_api = spilcd_interface()
		pass

	def open(self):
		self.spilcd_api.open()
		self.spilcd_api.lcd_init()
		self.spilcd_api.lcd_window_init(0, 0, 53, 159)
		self.spilcd_api.lcd_window_enable(True)
		pass

	def close(self):
		self.spilcd_api.lcd_window_enable(False)
		sell.spilcd_api.lcd_reset()
		self.spilcd_api.close()
		pass

	def show(self, image:list):
		#首先需要将160*160的点阵转换为160 * 81的点阵
		#其中，81的最后一个点是作为占位符，不显示在屏幕上
		img = [0] * (160 * 81)
		for i in range(160):
			pos = 0
			for j in range(160):
				if (j!=0) and (j%2==0):
					pos += 1
				val = image[i][j]
				if (j%2 != 0):
					img[i*81 + pos] |= val
				else:
					img[i*81 + pos] |= (val << 4)

		'''
		for i in range(160):
			for j in range(81):
				print("%02x"%(img[i*81 + j]), end="")
			print("")
		'''

		print("ready show image")
		self.spilcd_api.open_screen()
		self.spilcd_api.begin_write_data()
		self.spilcd_api.continue_write_data(img)
		self.spilcd_api.end_write_data()
		print("end show image")
