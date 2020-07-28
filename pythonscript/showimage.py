#!/usr/bin/env python3
#-*- coding:utf-8 -*-

import sys
import os
import shutil

import spilcd_api
import generate_pillow_buffer as sc
import watchdog

def initialization():
	spilcd_api.on()
	screen = sc.screen()
	screen.show_logo()
	spilcd_api.set_doorlock(0)
	wdtfile = "/home/watchdog/feed.py"
	enablewdt = False
	if os.path.exists(wdtfile):
		s = os.path.getsize(wdtfile)
		if s > 80:
			enablewdt = True
	if enablewdt == False:
		if os.path.exists("/root/watchdog/feed.py"):
			s = os.path.getsize("/root/watchdog/feed.py")
			if s > 80:
				enablewdt = True
				shutil.copyfile("/root/watchdog/feed.py", wdtfile)
	if enablewdt == True:	
		watchdog.open()
		
#显示出错标志
def show_error_icon():
	screen = sc.screen()
	screen.show_erroricon()
#显示设备logo
def show_space():
	screen = sc.screen()
	screen.show_logo()
#显示设备升级
def show_update():
	screen = sc.screen()
	screen.show_update()

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
	elif p == 4:
		show_update()
	else:
		print("else")
		pass
