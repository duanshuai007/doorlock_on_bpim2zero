#!/usr/bin/env python3
#-*- coding:utf-8 -*-

import sys
import os
import qrcode
import spilcd_api
#import socket_client
#import hardware.spilcd_dev as spilcd_dev
'''
	输入信息通过qrcode生成图像信息并通过PIL生成图像的object，
	PIL模块读取该object获取像素信息
'''

#sock = socket_client.socket_client()
#sock.connect_to_server(8899)
#lcd = spilcd_dev.spilcd_dev()
#lcd.open()

def create_2vcode_save_image(msg:str):
	#box_size是表示每个点的值的正方形色块的长宽，border代表最外层的白色边框的宽度是几个box_size
	try:
		qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_L, box_size=10, border=0)
		qr.add_data(data=msg)
		qr.make(fit=True)
		img = qr.make_image(fill_color="green", back_color="white")
		#img.save("./2vcode_temp.png")
		return img
	except Exception as e:
		print("create_2vcode_save_image error:{}".format(e))
		return None

def show_qrcode_2vcode_on_screen(msg:str)->bool:
	global s
	im = create_2vcode_save_image(msg)
	if im is not None:
		im = im.convert('L')
		im = im.resize((160, 160))
		#im.save("./2vcode_resize.png")
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
#if spilcd.on() == True:
#				return spilcd.show(imgbuffer)
			#sock.send_image_buffer(imgbuffer)
			#lcd.show(imgbuffer)
			spilcd_api.show(imgbuffer)	
			return False
		except Exception as e:
			del im
			print("show_qrcode_2vcode_on_screen error:{}".format(e))
			return False

if __name__ == "__main__":
	if len(sys.argv) < 2:
		print("please input image path")
		exit(1)
	spilcd_api.on()
	show_qrcode_2vcode_on_screen(sys.argv[1])
