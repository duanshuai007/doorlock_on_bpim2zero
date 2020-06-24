#!/usr/bin/env python3
#-*- coding:utf-8 -*-

from spilcd_interface import spilcd_interface

class spilcd_dev():

	def __init__(self):
		self.spilcd_interface = spilcd_interface()
		pass

	def open(self):
		self.spilcd_interface.lcd_init()
		self.spilcd_interface.lcd_window_init(0, 0, 53, 159)
		self.spilcd_interface.lcd_window_enable(True)
		pass

	def close(self):
		self.spilcd_interface.lcd_window_enable(False)
		sell.spilcd_interface.lcd_reset()
		self.spilcd_interface.close()
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
		self.spilcd_interface.open_screen()
		self.spilcd_interface.begin_write_data()
		self.spilcd_interface.continue_write_data(img)
		self.spilcd_interface.end_write_data()

	def disable_screen(self):
		self.spilcd_interface.close_screen()
		pass
