#!/usr/bin/env python3
#-*- coding:utf-8 -*-

import os
import sys
from PIL import Image

def show_image_on_screen(filename:str, fullscreen:bool, keepshape:bool):
	if not os.path.exists(filename):
		print("show_image_on_screen file[{}] not exists!".format(filename))
		return None
	try:
		imgbuffer = []
		im = Image.open(filename)
		im = im.convert('L')
		(w, h) = im.size
		print("img col={},row={}".format(im.size[0], im.size[1]))
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
				print("show_image_on_screen image too big")
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
		cur = 0 

		for row in range(160):
			if row < top or row >= (160 - top):
				imgbuffer.append([0x0] * 160)
			else:
				line = []
				line += [0x0] * left
				line += img[cur]
				line += [0x0] * left
				imgbuffer.append(line)
				cur += 1
		return imgbuffer
	except Exception as e:
		print("show_image_on_screen error:{}".format(e))
		return None


def write_buffer_to_file(filename:str, imgbuffer:list):
	try:
		if os.path.exists(filename):
			os.remove(filename)
		playbuffer = []
		for i in range(81*160):
			playbuffer.append(0)

		i = 0
		for line in imgbuffer:
			j = 0
			pos = 0
			for point in line:
				if (j!=0) and (j%2==0):
					pos += 1
				if (j % 2 != 0):
					val = int(playbuffer[i * 81 + pos])
					val |= int(point)
					playbuffer[i * 81 + pos] = val
				else:
					val = int(playbuffer[i * 81 + pos])
					val |= int(point << 4)
					playbuffer[i * 81 + pos] = val
				j += 1
			i += 1

		with open(filename, 'w+') as f:
			#imagebuffer = " ,".join(str(val) for val in playbuffer)
			imagebuffer = ""
			pos = 0
			for val in playbuffer:
				if pos % 81 == 0 and pos != 0:
					imagebuffer = "{}{}".format(imagebuffer, "\n")
				if len(imagebuffer) == 0:
					imagebuffer = "{}".format(str(val))
				else:
					imagebuffer = "{},{}".format(imagebuffer, str(val))
				pos += 1
			result = "{}{}{}".format("uint8_t imgbuf[] = {\n", imagebuffer, "\n};")
			f.write(result)
	except Exception as e:
		print("write_buffer_to_file error {}".format(e))

if __name__ == "__main__":
	fname = sys.argv[1]
	tarfilename = sys.argv[2]
	l = show_image_on_screen(fname, True, True)
	if l is not None:
		write_buffer_to_file(tarfilename, l)
