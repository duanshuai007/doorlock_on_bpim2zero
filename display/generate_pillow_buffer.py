#!/usr/bin/env python3
#-*- coding:utf-8 -*-

from PIL import Image
import sys
import os
import qrcode
import urllib.request as ur
import time
import threading

import display.downloadfile as dl
import LoggingQueue
import config
import spilcd_api

class screen():

#	__logo_buffer = []
#	__error_buffer = []

	def __init__(self):
		self.log = LoggingQueue.LoggingProducer().getlogger()
		spilcd_api.on()
#		self.__error_buffer = self.read_image_return_list("/root/display/error_160x160.png")
#		self.__logo_buffer = self.read_image_return_list("/root/display/logo_160x160.png")	

	'''
		通过qrcode生成二维码信息，不用保存图片，将生成
		图片信息的点阵作为spilcd的输入来显示二维码
	'''
	def create_2vcode_return_matrix(self, msg:str):
		#box_size是表示每个点的值的正方形色块的长宽，border代表最外层的白色边框的宽度是几个box_size
		try:
			qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_L, box_size=10, border=0)
			qr.add_data(data=msg)
			qr.make(fit=True)
			s = qr.get_matrix()
			return s
		except Exception as e:
			self.log.error("create_2vcode_return_matrix error:{}".format(e))
			return None

	def show_matrix_on_screen(self, imgmsg:str)->None:
		matrix = create_2vcode_return_matrix(imgmsg)
		if matrix is not None:
			#spilcd.display(matrix)
			pass

	'''
		输入信息通过qrcode生成图像信息并通过PIL生成图像的object，
		PIL模块读取该object获取像素信息
	'''
	def create_2vcode_save_image(self, msg:str):
		#box_size是表示每个点的值的正方形色块的长宽，border代表最外层的白色边框的宽度是几个box_size
		try:
			qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_L, box_size=10, border=0)
			qr.add_data(data=msg)
			qr.make(fit=True)
			img = qr.make_image(fill_color="green", back_color="white")
			#img.save("/root/2vcode_temp.jpg")
			return img
		except Exception as e:
			self.log.error("create_2vcode_save_image error:{}".format(e))
			return None

	def show_qrcode_2vcode_on_screen(self, msgdict:dict)->bool:
		im = self.create_2vcode_save_image(msgdict["data"])
		if im is not None:
			im = im.convert('L')
			im = im.resize((160, 160))
			imgbuffer = []
			try:
				for row in range(160):
					#for col in range(160, 0):
					col = 160
					line = []
					while col > 0:
						col -= 1
						pv = im.getpixel((col, row))
						if pv < 180:
							line.append(0xf)
						else:
							line.append(0x0)	
					imgbuffer.append(line)
				#print(imgbuffer)
				spilcd_api.show(imgbuffer)
				return True
			except Exception as e:
				self.log.error("show_qrcode_2vcode_on_screen error:{}".format(e))
				return False
		return False

	def read_image_return_list(self, filename):
		try:
			im = Image.open(filename)
			im = im.convert('L')
			(w,h) = im.size
			if w != 160 or h != 160:
				self.log.error("read_image_return_list input image size must be (160x160)")
				return None
			img = []
			for r in range(h):
				l = []
				c = w
				while c > 0:
					c -= 1
					pv = im.getpixel((c, r))
					if pv < 180:
						l.append(0xf)
					else:
						l.append(0x0)
				img.append(l)
			return img
		except Exception as e:
			self.log.error("read_image_return_list error:{}".format(e))
			return None

	'''
		输入图片的路径，通过PIL模块对图片处理
		获取图像像素信息
	'''
	def show_image_on_screen(self, filename:str, fullscreen:bool, keepshape:bool)->bool:
		if not os.path.exists(filename):
			self.log.error("show_image_on_screen file[{}] not exists!".format(filename))
			return False
		try:	
			imgbuffer = []
			im = Image.open(filename)
			im = im.convert('L')
			(w, h) = im.size
			#print("img col={},row={}".format(im.size[0], im.size[1]))
			f = 0.00
			r = 0
			if w != h:
				r = max(w, h)
				f = 160 / r
			else:
				f = 160 / w
			
			#是否改变图片的小大
			if fullscreen == True:
				#全屏幕显示
				if keepshape == True:
					im = im.resize((int(w * f), int(h * f)))
				else:
					im = im.resize((160, 160))
			else:
				#原图大小显示
				if r > 160:
					self.log.error("show_image_on_screen image too big")
					return False

			#im.save("output.jpg")
			(w, h) = im.size
			img = []
			#print("w={} h={}".format(w, h))
			for r in range(h):
				l = []
				c = w
				while c > 0:
					c -= 1
					pv = im.getpixel((c, r))
					if pv < 180:
						l.append(0xf)
					else:
						l.append(0x0)
				img.append(l)

			'''
			将图片的像素点放置在屏幕的中央
			'''
			left = int((160 - w) / 2)
			top = int((160 - h) / 2)
			#print("left={} top={}".format(left, top))
			#print(len(img))
			cur = 0
			
			for row in range(160):
				if row < top or row >= (160 - top):
					imgbuffer.append([0x0] * 160)
				else:
					line = []
					line += [0x0] * left
					line += img[cur]
					line += [0x0] * left
					#print("line={}".format(line))
					imgbuffer.append(line)
					cur += 1
			#print(imgbuffer)
			spilcd_api.show(imgbuffer)
			return True
		except Exception as e:
			self.log.error("show_image_on_screen error:{}".format(e))
			return False

	def show_white(self):
		imgbuffer = []
		for i in range(160):
			line = [0] * 160
			imgbuffer.append(line)
		spilcd_api.show(imgbuffer)

	def show_black(self):
		line = [0xf] * 160
		imgbuffer = line * 160
		spilcd_api.show(imgbuffer)

	def down_image_and_show_image_on_screen(self, msgdict:dict)->bool:
		#print("down_image_and_show_image_on_screen url:{}".format(url))
		if dl.download(msgdict["download"], "/tmp/test.jpg") == True:
			return self.show_image_on_screen("/tmp/test.jpg", True, True)
		else:
			return False
	
	def show_erroricon(self):
		self.show_image_on_screen("/root/display/error_160x160.png", True, True)
#		if self.__error_buffer is not None:
#			spilcd_api.show(self.__error_buffer)
		pass
	def show_logo(self):
		self.show_image_on_screen("/root/display/logo_160x160.png", True, True)
#		if self.__logo_buffer is not None:
#			spilcd_api.show(self.__logo_buffer)
		pass

if __name__ == "__main__":
	if len(sys.argv) < 2:
		print("please input image path")
		exit(1)
	#print("file name:{}".format(sys.argv[1]))	
	c = sys.argv[2]
	#print("c={}".format(c))
	if c == '1':
		show_image_on_screen(sys.argv[1], fullscreen=True, keepshape=True)
	elif c == '2':
		show_qrcode_2vcode_on_screen(sys.argv[1])
	else:
		show_matrix_on_screen(sys.argv[1])
