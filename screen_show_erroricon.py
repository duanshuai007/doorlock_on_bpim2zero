#!/usr/bin/env python3
#-*- coding:utf-8 -*-

import spilcd_api
import display.generate_pillow_buffer as sc

def initialization():
	spilcd_api.on()
	spilcd_api.set_doorlock(1)
	screen = sc.screen()
	screen.show_image_on_screen("/root/display/error.png", True, True)

if __name__ == "__main__":
	initialization()
