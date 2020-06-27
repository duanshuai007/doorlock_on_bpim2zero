#!/usr/bin/env python3
#-*- coding:utf-8 -*-

import sys
import os
import spilcd_api
import display.generate_pillow_buffer as sc
import watchdog

def initialization():
	spilcd_api.on()
	spilcd_api.set_doorlock(1)
	#spilcd_api.close_screen()
	screen = sc.screen()
	#screen.show_image_on_screen("/root/display/logo_160x160.jpg", True, True)
	screen.show_logo()
	watchdog.open()

def show_error_icon():
	screen = sc.screen()
	#screen.show_image_on_screen("/root/display/error_160x160.png", True, True)
	screen.show_erroricon()

def show_space():
	#spilcd_api.on()
	#spilcd_api.close_screen()
	#spilcd_api.set_doorlock(1)
	screen = sc.screen()
	screen.show_logo()

if __name__ == "__main__":
	if len(sys.argv) < 2:
		print("showimage.py need 1 paramters")
		exit(1)
	
	p = int(sys.argv[1])
	#print("p={}".format(p))
	if p == 1:
		initialization()
	elif p == 2:
		show_error_icon()
	elif p == 3:
		show_space()
	else:
		print("else")
		pass
