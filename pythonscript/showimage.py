#!/usr/bin/env python3
#-*- coding:utf-8 -*-

import sys
import os
import shutil

import spilcd_api
import generate_pillow_buffer as sc
import watchdog
import config

def initialization():
	spilcd_api.on()
	screen = sc.screen()
	if os.path.exists("/tmp/wx2vcode.jpg"):
		screen.show_image("/tmp/wx2vcode.jpg")
	else:
		screen.show_logo()
	cfg = config.config("/root/config.ini")
	close_door_level = int(cfg.get("DOORLOCK", "CLOSE_LEVEL"))
	spilcd_api.set_doorlock(close_door_level)
	wdten = cfg.get("WATCHDOG", "ENABLE")
	if wdten == "true":
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
def display_error_image():
	screen = sc.screen()
	screen.show_erroricon()
#显示设备logo
def display_logo_image():
	screen = sc.screen()
	screen.show_logo()
#显示设备升级
def display_update_image():
	screen = sc.screen()
	screen.show_update()

if __name__ == "__main__":
	if len(sys.argv) < 2:
		print("showimage.py need 1 paramters")
		exit(1)
	
	p = sys.argv[1]
	#print("p={}".format(p))
	if p == "init":
		initialization()
	elif p == "error":
		display_error_image()
	elif p == "logo":
		display_logo_image()
	elif p == "update":
		display_update_image()
	else:
		pass
