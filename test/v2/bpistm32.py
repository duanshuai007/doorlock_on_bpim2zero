#!/usr/bin/env python3
#-*- coding:utf-8 -*-

import json
import requests
import math
#import binascii

url=
msg = {
	"device_sn":
}

show_2vcode_image = [

0xff,0xff,0xff,0xff,0xff,0xff,0xff,0xff,0xff,0xff,0xff,0xff,0xff,0xff,0xff,0xff,0xff,0xff,0xff,0xff,
	0xff,0xff,0xff,0xff,0xff,0xff,0xff,0xff,0xff,0xff,0xff,0xff,0xff,0xff,0xff,0xff,0xff,0xff,0xff,0xff,
	0xff,0xff,0xff,0xff,0xff,0xff,0xff,0xff,0xff,0xff,0xff,0xff,0xff,0xff,0xff,0xff,0xff,0xff,0xff,0xff,
	0xff,0xff,0xff,0xff,0xff,0xff,0xff,0xff,0xff,0x3c,0x78,0xff,0xff,0xff,0xff,0xff,0xff,0xff,0xff,0xff,
	0xff,0xff,0xff,0xff,0xff,0xff,0xff,0xff,0xff,0x1c,0x38,0xff,0xff,0xff,0xff,0xff,0xff,0xff,0xff,0xff,
	0xff,0xff,0xff,0xff,0xff,0xff,0xff,0xf7,0xfe,0x1c,0x38,0xff,0xef,0xff,0xff,0xff,0xff,0xff,0xff,0xff,
	0xff,0xff,0xff,0xff,0xff,0xff,0xff,0xe3,0xff,0x1c,0x30,0xff,0xc7,0xff,0xff,0xff,0xff,0xff,0xff,0xff,
	0xff,0xff,0xff,0xff,0xff,0xff,0xf9,0xe3,0xff,0x1c,0x30,0xff,0x87,0xbf,0xff,0xff,0xff,0xff,0xff,0xff,
	0xff,0xff,0xff,0xff,0xff,0xff,0xf8,0xe1,0xff,0x1e,0x70,0xff,0x87,0x1f,0xff,0xff,0xff,0xff,0xff,0xff,
	0xff,0xff,0xff,0xff,0xff,0xff,0xf0,0xe1,0xff,0x0f,0xf0,0xff,0x86,0x1f,0xff,0xff,0xff,0xff,0xff,0xff,
	0xff,0xff,0xff,0xff,0xff,0xff,0xf8,0x61,0xff,0x0f,0xf0,0xff,0x8e,0x1c,0x7f,0xff,0xff,0xff,0xff,0xff,
	0xff,0xff,0xff,0xff,0xff,0xff,0xf8,0x7f,0xff,0x0f,0xf9,0xff,0xde,0x1c,0x3f,0xff,0xff,0xff,0xff,0xff,
	0xff,0xff,0xff,0xff,0xff,0xff,0xf8,0x7f,0xff,0x0f,0xff,0xff,0xfc,0x38,0x7f,0xff,0xff,0xff,0xff,0xff,
	0xff,0xff,0xff,0xff,0xff,0xff,0xfc,0x3f,0xff,0x0f,0xff,0xff,0xfc,0x38,0x7f,0xff,0xff,0xff,0xff,0xff,
	0xff,0xff,0xff,0xff,0xff,0xff,0xfc,0x3f,0xff,0x0f,0xff,0xff,0x3c,0x38,0xff,0xff,0xff,0xff,0xff,0xff,
	0xff,0xff,0xff,0xff,0xff,0xff,0xfe,0x1f,0xff,0x8c,0x7f,0xfe,0x18,0x79,0xff,0xff,0xff,0xff,0xff,0xff,
	0xff,0xff,0xff,0xff,0xff,0xff,0xfe,0x1f,0xff,0x8c,0x7f,0xfe,0x18,0x7f,0xff,0xff,0xff,0xff,0xff,0xff,
	0xff,0xff,0xff,0xf8,0x1f,0xff,0xfe,0x1f,0xff,0x8e,0x7f,0xfe,0x38,0x7f,0xff,0xff,0xff,0xff,0xff,0xff,
	0xff,0xff,0xff,0xc0,0x03,0xff,0xff,0x0f,0xff,0xff,0xf1,0xfc,0x3c,0xe7,0xff,0xff,0xff,0xff,0xff,0xff,
	0xff,0xff,0xff,0x00,0x00,0xff,0xff,0x0f,0xff,0xff,0xf1,0xfc,0x3f,0xc3,0xff,0xff,0xff,0xff,0xff,0xff,
	0xff,0xff,0xfe,0x00,0x00,0x7f,0xff,0x0f,0xff,0xff,0xf3,0xfc,0x3f,0xc3,0xff,0xff,0xff,0xff,0xff,0xff,
	0xff,0xff,0xf8,0x00,0x00,0x3f,0xe1,0xff,0xff,0x8c,0x7f,0xfc,0x63,0x87,0xff,0xff,0xff,0xff,0xff,0xff,
	0xff,0xff,0xf8,0x00,0x00,0x1f,0xe1,0xff,0xff,0x8c,0x7f,0xf8,0x63,0x8f,0xff,0xff,0xff,0xff,0xff,0xff,
	0xff,0xff,0xf0,0x00,0x7f,0x0f,0xf3,0xfe,0x1f,0x8e,0x7f,0xf8,0x43,0xcf,0xff,0xff,0xff,0xff,0xff,0xff,
	0xff,0xff,0xe0,0x00,0xff,0x87,0xff,0xfe,0x1f,0xff,0xe3,0xf8,0x43,0xff,0xf0,0xff,0xff,0xff,0xff,0xff,
	0xff,0xff,0xe0,0x01,0xff,0xc7,0xff,0xfe,0x1f,0xff,0xe1,0xf8,0xc3,0xff,0xf0,0xf8,0x7f,0xff,0xff,0xff,
	0xff,0xff,0xc0,0x01,0xc1,0xc3,0xff,0xff,0x1f,0xff,0xe3,0xf0,0x87,0xff,0xe1,0xe0,0x1f,0xff,0xff,0xff,
	0xff,0xff,0xc0,0x03,0xc1,0xe3,0xff,0xff,0x1f,0xc4,0x63,0xf0,0x87,0xff,0xe1,0xc0,0x0f,0xff,0xff,0xff,
	0xff,0xff,0xc0,0x03,0xc1,0xe3,0xff,0xff,0xbf,0xc4,0x63,0xf1,0x8f,0xff,0xe3,0x87,0x87,0xff,0xff,0xff,
	0xff,0xff,0x80,0x03,0xc1,0xc3,0xff,0xff,0xff,0xce,0x67,0xe1,0x0f,0xff,0xff,0x0f,0xc3,0xff,0xff,0xff,
	0xff,0xff,0x80,0x03,0xc7,0xc3,0xff,0xff,0xff,0xff,0xff,0xf1,0x0f,0xff,0xff,0x1f,0xe3,0xff,0xff,0xff,
	0xff,0xff,0x80,0xf3,0xcf,0x83,0xff,0x9f,0xff,0xff,0xff,0xfb,0x1f,0xff,0xff,0x1c,0xe3,0xff,0xff,0xff,
	0xff,0xff,0x81,0xf3,0xcf,0x03,0xff,0x0f,0xff,0xff,0xff,0xff,0xbf,0xff,0xff,0x38,0x73,0xff,0xff,0xff,
	0xff,0xff,0x83,0xe3,0xc0,0x03,0xff,0x0f,0xff,0xc7,0xff,0xff,0xff,0xfe,0xff,0x1c,0xe3,0xff,0xff,0xff,
	0xff,0xff,0x83,0x83,0xc0,0x03,0xff,0x87,0xe7,0xc7,0xff,0xff,0xe3,0xf8,0x7f,0x1f,0xe3,0xff,0xff,0xff,
	0xff,0xff,0xc7,0x83,0xc0,0x03,0xff,0x87,0xc3,0xe7,0xff,0xff,0xc3,0xf8,0x7f,0x1f,0xe3,0xf1,0xff,0xff,
	0xff,0xff,0xc7,0x83,0xc0,0x03,0x8f,0xc7,0xc7,0xff,0xff,0xff,0xc3,0xf0,0xcf,0x8f,0xc7,0xe0,0xff,0xff,
	0xff,0xff,0xc3,0x83,0x80,0x07,0x07,0xff,0xff,0xff,0xff,0xff,0xc3,0xe0,0x87,0x80,0x07,0x81,0xff,0xff,
	0xff,0xff,0xe3,0xff,0x80,0x07,0x87,0xff,0xff,0xf7,0xff,0xff,0x87,0xe1,0x87,0xc0,0x0f,0x03,0xff,0xff,
	0xff,0xff,0xe1,0xff,0x00,0x0f,0x83,0xff,0xff,0xe3,0xc7,0xff,0x87,0xc3,0xfd,0xf0,0x3c,0x07,0xff,0xff,
	0xff,0xff,0xf0,0xfe,0x00,0x0f,0xc1,0xff,0xf1,0xe3,0xc7,0x8f,0x0f,0x83,0xf8,0xff,0xf8,0x1f,0xbf,0xff,
	0xff,0xff,0xf8,0x00,0x00,0x1f,0xe1,0xff,0xf1,0xe7,0xcf,0x0f,0x0f,0x87,0xf8,0xff,0xf0,0x3e,0x1f,0xff,
	0xff,0xff,0xfc,0x00,0x00,0x3f,0xf0,0xfc,0xf1,0xff,0xff,0x9e,0x1f,0x8f,0xfd,0xff,0xe0,0xf8,0x1f,0xff,
	0xff,0xff,0xfe,0x00,0x00,0x7f,0xf0,0x78,0x7f,0xff,0xff,0xfe,0x1f,0x9f,0xff,0xff,0xc1,0xe0,0x3f,0xff,
	0xff,0xff,0xff,0x00,0x01,0xff,0xf8,0x7c,0xff,0xff,0xff,0xfe,0x3f,0xff,0xff,0xff,0xe3,0xe0,0x7f,0xff,
	0xff,0xff,0xff,0xc0,0x07,0xff,0xfc,0x3f,0xff,0xc0,0x03,0xff,0xfd,0xff,0xff,0xfc,0xff,0xe1,0xff,0xff,
	0xff,0xc7,0xff,0xff,0xff,0xfc,0x7c,0x1f,0xfc,0x00,0x00,0x3f,0xf8,0xfc,0x3f,0xf0,0x7f,0xe7,0xe7,0xff,
	0xff,0xc1,0xff,0xff,0xff,0xfc,0x3e,0x1f,0xe0,0x00,0x00,0x07,0xf8,0xf8,0x3f,0xe0,0x7f,0xff,0x83,0xff,
	0xff,0xc0,0x7f,0xff,0xff,0xfc,0x1f,0x3f,0x80,0x00,0x00,0x00,0xfd,0xf0,0x3f,0xe0,0xe3,0xfe,0x03,0xff,
	0xff,0xe0,0x3f,0xff,0xff,0xfe,0x0f,0xfe,0x00,0x00,0x00,0x00,0x7f,0xe0,0x7f,0xe3,0xe3,0xfc,0x07,0xff,
	0xff,0xf0,0x3f,0xff,0xff,0xff,0x07,0xf8,0x00,0x00,0x00,0x00,0x1f,0xe0,0xff,0xff,0xe3,0xf8,0x1f,0xff,
	0xff,0xfe,0x39,0xfe,0x3f,0xff,0x87,0xf0,0x00,0x00,0x00,0x00,0x07,0xc1,0xff,0xff,0xff,0xfc,0x7f,0xff,
	0xff,0xff,0xf8,0x7e,0x0f,0x8f,0xc7,0xc0,0x00,0x00,0x00,0x00,0x03,0xe3,0xf1,0xf3,0xff,0xff,0xff,0xff,
	0xff,0xff,0xf8,0x3e,0x07,0x07,0xff,0x80,0x00,0x00,0x00,0x00,0x01,0xff,0xe1,0xe3,0xf0,0x7f,0xff,0xff,
	0xff,0xff,0xf8,0x3f,0x87,0x81,0xff,0x00,0x00,0x00,0x00,0x00,0x00,0xff,0x81,0xe3,0xe0,0x7f,0xff,0xff,
	0xff,0xff,0xfe,0x3f,0xff,0xc0,0xfe,0x00,0x00,0x00,0x00,0x00,0x00,0x7f,0x03,0xf7,0xc0,0xff,0xff,0xff,
	0xff,0xff,0xff,0xff,0xff,0xe0,0x7c,0x00,0x00,0x00,0x00,0x00,0x00,0x3e,0x07,0xfc,0xe3,0xff,0xff,0xff,
	0xff,0xff,0xff,0xff,0xff,0xf8,0x78,0x00,0x00,0x00,0x00,0x00,0x00,0x1e,0x1f,0xf0,0xff,0xff,0xff,0xff,
	0xff,0xff,0xff,0xff,0xff,0xfc,0xf0,0x00,0x00,0x00,0x00,0x00,0x00,0x0f,0x3f,0xe0,0xff,0xff,0xff,0xff,
	0xfc,0x1f,0xff,0xff,0xf8,0xff,0xf0,0x00,0x00,0x00,0x00,0x00,0x00,0x07,0xff,0xc1,0xff,0xff,0xf8,0x3f,
	0xf8,0x1f,0xff,0xff,0xf0,0xff,0xe0,0x00,0x00,0x00,0x00,0x00,0x00,0x07,0xf8,0xe3,0xff,0xff,0xf0,0x3f,
	0xfc,0x1c,0x1f,0xff,0xf9,0xef,0xc0,0x00,0x00,0x00,0x00,0x00,0x00,0x03,0xe0,0xff,0xff,0xf8,0x70,0x3f,
	0xff,0x1c,0x0f,0xff,0xff,0xc7,0xc0,0x00,0x00,0x00,0x00,0x00,0x00,0x01,0xe0,0xff,0xff,0xf0,0x38,0xff,
	0xff,0xfc,0x0f,0xff,0xff,0xc7,0x80,0x01,0xff,0xff,0xff,0x00,0x20,0x01,0xe1,0xff,0xf8,0xf0,0x3f,0xff,
	0xff,0xfe,0x0f,0xc3,0xff,0xef,0x80,0x07,0xff,0xff,0xff,0x80,0xf0,0x00,0xe7,0xff,0xe0,0x70,0xff,0xff,
	0xf0,0x7f,0xff,0x81,0xff,0xff,0x00,0x07,0xff,0xff,0xff,0xc0,0xf8,0x00,0xff,0xff,0xe0,0x7f,0xfc,0x1f,
	0xf0,0x0f,0xff,0xc0,0xff,0xff,0x00,0x0f,0xff,0xff,0xff,0xc0,0xf8,0x00,0x7f,0xc7,0xe0,0xff,0x80,0x0f,
	0xf0,0x07,0xff,0xe1,0xff,0xfe,0x00,0x0f,0xff,0xff,0xff,0xc0,0xf8,0x00,0x7e,0x03,0xff,0xff,0x00,0x0f,
	0xf8,0x07,0xfc,0x3f,0xff,0x1e,0x00,0x0f,0xff,0xff,0xff,0xc0,0xf8,0x00,0x78,0x03,0xff,0xc7,0x00,0x3f,
	0xff,0xcf,0xf8,0x1f,0xff,0x1e,0x00,0x0f,0xff,0xff,0xff,0xc0,0xf8,0x00,0x38,0x07,0xff,0xc7,0x87,0xff,
	0xff,0xff,0xf8,0x0f,0xff,0x1c,0x00,0x0f,0xff,0xff,0xff,0xc0,0xf8,0x00,0x38,0x7f,0xff,0xc7,0xff,0xff,
	0xff,0xff,0xfc,0x1f,0xff,0xfc,0x00,0x0f,0xff,0xff,0xff,0xc0,0xf8,0x00,0x3f,0xff,0xff,0xff,0xff,0xdf,
	0xff,0xff,0xff,0xff,0xff,0xfc,0x00,0x0f,0xff,0xff,0xff,0xc0,0xf8,0x00,0x1f,0xff,0xff,0xff,0x1e,0x0f,
	0xff,0xff,0xf8,0x3f,0xff,0xfc,0x00,0x0f,0xff,0xff,0xff,0xc0,0xf8,0x00,0x1f,0xff,0xff,0x00,0x0c,0x07,
	0xff,0xff,0xf8,0x1c,0x1f,0xf8,0x00,0x0f,0xff,0xff,0xff,0xc0,0xf8,0x00,0x1f,0xf9,0xc7,0x00,0x0e,0x0f,
	0xff,0xff,0xf8,0x1c,0x0e,0x38,0x00,0x0f,0xff,0xff,0xff,0xc0,0xf8,0x00,0x1c,0x71,0xc7,0x00,0x1f,0xff,
	0xff,0xff,0xfe,0x3c,0x0c,0x38,0x00,0x0f,0xff,0xff,0xff,0xc0,0xf8,0x00,0x1c,0x71,0xc7,0x9f,0xff,0xff,
	0xff,0xff,0xff,0xff,0xbe,0x78,0x00,0x0f,0xff,0xff,0xff,0xc0,0xf8,0x00,0x1c,0x7b,0xff,0xff,0xff,0xff,
	0xff,0xff,0xff,0xff,0xff,0xf8,0x00,0x0f,0xff,0xff,0xff,0xc0,0xf8,0x00,0x1f,0xff,0xff,0xff,0xff,0xff,
	0xff,0xff,0xff,0xff,0xff,0xf8,0x00,0x0f,0xff,0xff,0xff,0xc0,0xf8,0x00,0x1f,0xff,0xff,0xff,0xff,0xff,
	0xff,0xff,0xff,0xff,0xff,0xf8,0x00,0x0f,0xff,0xff,0xff,0xc0,0xf8,0x00,0x1f,0xff,0xff,0xff,0xff,0xff,
	0xff,0xff,0xff,0xff,0xff,0xf8,0x00,0x0f,0xff,0xff,0xff,0xc0,0xf8,0x00,0x1f,0x7f,0xff,0xff,0xff,0xff,
	0xff,0xff,0xff,0xff,0xfe,0x38,0x00,0x0f,0xff,0xff,0xff,0xc1,0xf8,0x00,0x1c,0x00,0x3f,0xff,0xff,0xff,
	0xff,0xff,0xfc,0x3f,0xfc,0x38,0x00,0x0f,0xff,0xff,0xff,0xc3,0xf0,0x00,0x1c,0x00,0x07,0x80,0xff,0xff,
	0xff,0xff,0xf8,0x1f,0xfe,0x78,0x00,0x07,0xff,0xff,0xff,0xc7,0xf0,0x00,0x1c,0x00,0x07,0x00,0x1f,0x3f,
	0xff,0xff,0xf8,0x1f,0xff,0xf8,0x00,0x07,0xff,0xff,0xff,0x9f,0xe0,0x00,0x1f,0xf0,0x07,0x00,0x0e,0x0f,
	0xff,0xff,0xfc,0x7f,0xff,0xfc,0x00,0x03,0xff,0xff,0xff,0x3f,0xc0,0x00,0x1f,0xff,0xff,0x80,0x0e,0x07,
	0xff,0xff,0xff,0xf7,0xff,0xfc,0x00,0x01,0xff,0xff,0xfe,0x7f,0x00,0x00,0x1f,0xff,0xc3,0xff,0xfe,0x0f,
	0xff,0xff,0xff,0xe3,0xff,0xbc,0x00,0x00,0xff,0xff,0xfc,0xfe,0x00,0x00,0x3d,0xff,0x81,0xff,0xff,0xff,
	0xff,0xff,0x3f,0xe3,0xfc,0x1c,0x00,0x00,0x7f,0xff,0xfb,0xfc,0x00,0x00,0x38,0x1f,0x80,0xfd,0xff,0xff,
	0xff,0xfe,0x1f,0xf7,0xf8,0x1e,0x00,0x00,0x3f,0xff,0xf7,0xf8,0x00,0x00,0x38,0x07,0xc1,0xf8,0xff,0xff,
	0xff,0xfe,0x1f,0xff,0xf8,0x3e,0x00,0x00,0x0f,0xff,0xcf,0xe0,0x00,0x00,0x78,0x03,0xff,0xf8,0xff,0xff,
	0xff,0xff,0x3f,0xc1,0xfc,0xfe,0x00,0x00,0x1f,0xff,0xff,0xc0,0x00,0x00,0x7f,0x03,0x1f,0xfd,0xff,0xff,
	0xff,0xff,0xfc,0x00,0xff,0xff,0x00,0x00,0x3f,0xff,0xff,0x80,0x00,0x00,0x7f,0xe7,0x0c,0x7f,0xff,0xff,
	0xff,0xff,0xe0,0x01,0xff,0xff,0x00,0x00,0x3f,0xff,0xff,0x00,0x00,0x00,0xff,0xff,0x9c,0x7f,0xff,0xff,
	0xff,0xff,0x80,0x07,0xff,0xc7,0x00,0x00,0x3e,0xfd,0xfc,0x00,0x00,0x00,0xe3,0xff,0xfc,0x7f,0xff,0xff,
	0xff,0xff,0x80,0x7f,0xff,0x07,0x80,0x00,0x3c,0x78,0xf8,0x00,0x00,0x01,0xc0,0xff,0xff,0xff,0xcf,0xff,
	0xfe,0x1f,0x87,0xff,0xfe,0x07,0xc0,0x00,0x00,0x00,0x00,0x00,0x00,0x01,0xe0,0x3f,0xff,0xff,0x87,0xff,
	0xfc,0x0f,0xff,0xff,0xfe,0x0f,0xc0,0x00,0x00,0x00,0x00,0x00,0x00,0x03,0xf0,0x1f,0xff,0xff,0x87,0xff,
	0xf8,0x1f,0xff,0xff,0xc7,0x3f,0xe0,0x00,0x00,0x00,0x00,0x00,0x00,0x03,0xfc,0x1f,0xff,0xff,0xff,0xff,
	0xfc,0x3f,0xff,0xff,0xc7,0xff,0xe0,0x00,0x00,0x00,0x00,0x00,0x00,0x07,0xff,0x1f,0xff,0xff,0xff,0xff,
	0xff,0xff,0xff,0xff,0xc7,0xfc,0xf0,0x00,0x00,0x00,0x00,0x00,0x00,0x0f,0x3f,0xff,0xff,0xff,0xff,0xff,
	0xff,0xff,0xff,0xff,0xff,0xf0,0x78,0x00,0x00,0x00,0x00,0x00,0x00,0x1e,0x3f,0xff,0xf7,0xff,0xff,0xff,
	0xff,0xff,0xff,0xff,0xff,0xe0,0xfc,0x00,0x00,0x00,0x00,0x00,0x00,0x1e,0x3f,0xff,0xe1,0xff,0xff,0xff,
	0xff,0xff,0xfe,0x3f,0xcf,0x80,0xfe,0x00,0x00,0x00,0x00,0x00,0x00,0x3f,0xfb,0xff,0xe0,0x7f,0xff,0xff,
	0xff,0xff,0xfe,0x3f,0x87,0x83,0xff,0x00,0x00,0x00,0x00,0x00,0x00,0x7f,0xf1,0xff,0xe0,0x1f,0xff,0xff,
	0xff,0xff,0xee,0x3f,0x87,0x87,0xef,0x80,0x00,0x00,0x00,0x00,0x00,0xff,0xf1,0xff,0xf8,0x1f,0xff,0xff,
	0xff,0xff,0xc7,0xf9,0xff,0x9f,0x87,0xc0,0x00,0x00,0x00,0x00,0x03,0xe3,0xf9,0xff,0x9e,0x1f,0xff,0xff,
	0xff,0xff,0xc7,0xf0,0xf1,0xff,0x07,0xe0,0x00,0x00,0x00,0x00,0x07,0xc1,0xff,0xff,0x0f,0xff,0xff,0xff,
	0xff,0xff,0xe7,0xf1,0xc1,0xfe,0x07,0xf8,0x00,0x00,0x00,0x00,0x0f,0xe0,0xff,0xff,0x1f,0xff,0x0f,0xff,
	0xff,0xff,0xfe,0x3f,0x81,0xfc,0x0f,0xfc,0x00,0x00,0x00,0x00,0x3f,0xf0,0x7f,0xff,0xfc,0x7f,0x07,0xff,
	0xff,0xff,0xfe,0x3e,0x03,0xfc,0x1f,0x3f,0x00,0x00,0x00,0x00,0xfc,0xf8,0x3f,0xfe,0xf8,0x3f,0x03,0xff,
	0xff,0xff,0xfe,0x3e,0x0f,0xfc,0x3e,0x1f,0xc0,0x00,0x00,0x03,0xf8,0x7c,0x3f,0xfc,0x7c,0x1f,0xc3,0xff,
	0xff,0xff,0xff,0xfe,0x1f,0xfc,0x7c,0x3f,0xf8,0x00,0x00,0x1f,0xf8,0x3e,0x3f,0xfc,0x7e,0x1f,0xf7,0xff,
	0xff,0xff,0xff,0xff,0x7f,0xff,0xfc,0x3f,0xff,0x00,0x00,0xff,0xfc,0x3f,0xff,0xfe,0xff,0x1d,0xff,0xff,
	0xff,0xfe,0x1f,0xc7,0xff,0x87,0xfc,0x78,0x7f,0xff,0xff,0xfe,0x3e,0x1f,0xff,0xff,0xe3,0xf8,0x7f,0xff,
	0xff,0xf8,0x1f,0xc7,0xff,0x07,0xfe,0xf8,0x7f,0xff,0xff,0xfe,0x1e,0x0f,0xff,0xff,0xc1,0xf8,0x1f,0xff,
	0xff,0xf8,0x3f,0xc7,0xff,0x07,0xff,0xfc,0xf1,0xff,0xff,0x8e,0x1f,0x0f,0xfc,0xff,0xe0,0x7c,0x1f,0xff,
	0xff,0xf8,0xff,0xff,0xfe,0x08,0xe7,0xff,0xf1,0xe3,0xc7,0x0f,0x0f,0x87,0xf8,0xff,0xf0,0x3e,0x1f,0xff,
	0xff,0xff,0xff,0xff,0xff,0x18,0xc7,0xff,0xf1,0xe3,0xc7,0x8f,0x8f,0x87,0xf8,0xff,0xf8,0x0f,0xff,0xff,
	0xff,0xff,0xe3,0xf8,0x0f,0xf8,0x87,0xe3,0xff,0xe3,0x87,0x87,0xff,0xc7,0xcf,0xf0,0x3e,0x07,0xff,0xff,
	0xff,0xff,0x83,0xf0,0x03,0xff,0x87,0xc3,0xff,0xff,0xc7,0x87,0xff,0xff,0x87,0xc0,0x0f,0x03,0xff,0xff,
	0xff,0xff,0x03,0xe0,0x81,0xff,0x0f,0xc3,0xff,0xff,0xc7,0x87,0xf7,0xff,0x87,0x80,0x07,0xc1,0xff,0xff,
	0xff,0xff,0x07,0xc3,0xf1,0xfe,0x0f,0xc3,0xff,0xff,0xc7,0xc3,0xe3,0xfc,0xff,0x8f,0xc7,0xe0,0xff,0xff,
	0xff,0xff,0x9f,0xc7,0xf8,0xfc,0x1f,0xc7,0xff,0xe7,0xc3,0xc3,0xe3,0xfc,0x7f,0x1f,0xe3,0xf1,0xff,0xff,
	0xff,0xff,0xff,0x8f,0x78,0xfc,0x3f,0xcf,0xff,0xc3,0xc3,0xe7,0xe7,0xfc,0x3f,0x1c,0xe3,0xff,0xff,0xff,
	0xff,0xff,0xff,0x8e,0x38,0xf8,0x7f,0xff,0xff,0xc7,0xc7,0xff,0xff,0xfc,0x1f,0x18,0x63,0xff,0xff,0xff,
	0xff,0xff,0xff,0x8e,0x38,0xf8,0x7f,0xf9,0xff,0xff,0xff,0xff,0xff,0xfe,0x1f,0x18,0x63,0xff,0xff,0xff,
	0xff,0xff,0xff,0x8f,0x78,0xfc,0xfe,0x30,0xff,0xff,0xff,0xff,0xfc,0xff,0x3f,0x1c,0xe3,0xff,0xff,0xff,
	0xff,0xff,0xff,0xc7,0xf8,0xff,0xfe,0x38,0xff,0xff,0xff,0xff,0xf8,0x7f,0xff,0x1f,0xe3,0xff,0xff,0xff,
	0xff,0xff,0xff,0xc3,0xf1,0xff,0xfc,0x3f,0xff,0xc6,0x63,0xff,0x88,0x7f,0xf7,0x8f,0xc7,0xff,0xff,0xff,
	0xff,0xff,0xff,0xe0,0x81,0xff,0xfc,0x3f,0x1f,0xc4,0x23,0xf9,0x8c,0x3f,0xe3,0x80,0x07,0xff,0xff,0xff,
	0xff,0xff,0xff,0xf0,0x03,0xff,0xf8,0x7f,0x1f,0x84,0x63,0xf0,0xcc,0x3f,0xe1,0xc0,0x0f,0xff,0xff,0xff,
	0xff,0xff,0xff,0xf8,0x0f,0x1f,0xf8,0x42,0x1f,0x87,0xe1,0xf8,0xfe,0x7f,0xe0,0xf0,0x3f,0xff,0xff,0xff,
	0xff,0xff,0xff,0xff,0xfe,0x1f,0xf0,0xc2,0x1f,0x87,0xe1,0xff,0xff,0xff,0xf0,0xff,0xff,0xff,0xff,0xff,
	0xff,0xff,0xff,0xff,0xfe,0x1f,0xf8,0xc2,0x1f,0xcf,0xe1,0xff,0xff,0xff,0xf8,0x7f,0xff,0xff,0xff,0xff,
	0xff,0xff,0xff,0xff,0xfc,0x3f,0xf9,0x86,0x3f,0xfe,0x61,0xff,0xff,0x8f,0xf8,0x7f,0xff,0xff,0xff,0xff,
	0xff,0xff,0xff,0xff,0xfc,0x3f,0xff,0x84,0x3f,0xfc,0x21,0xff,0xff,0x8f,0xfc,0x7f,0xff,0xff,0xff,0xff,
	0xff,0xff,0xff,0xff,0xfe,0x7f,0xef,0xcc,0x3f,0xfc,0x73,0xff,0xff,0x8f,0xfe,0x7f,0xff,0xff,0xff,0xff,
	0xff,0xff,0xff,0xff,0xff,0xff,0xc7,0xfc,0x3f,0xff,0xff,0xff,0xff,0xff,0xff,0xff,0xff,0xff,0xff,0xff,
	0xff,0xff,0xff,0xff,0xff,0xff,0xc7,0xfc,0x7f,0xff,0xff,0xfe,0x3f,0xff,0xff,0xff,0xff,0xff,0xff,0xff,
	0xff,0xff,0xff,0xff,0xff,0xff,0xe7,0xf8,0x7f,0xff,0xff,0xfe,0x3f,0xfb,0xff,0xff,0xff,0xff,0xff,0xff,
	0xff,0xff,0xff,0xff,0xff,0xff,0xff,0xf8,0x7f,0xff,0xf1,0xfe,0x3f,0xf1,0xff,0xff,0xff,0xff,0xff,0xff,
	0xff,0xff,0xff,0xff,0xff,0xff,0xff,0xf8,0x7f,0xff,0xe1,0xff,0xff,0xf1,0xff,0xff,0xff,0xff,0xff,0xff,
	0xff,0xff,0xff,0xff,0xff,0xff,0x1e,0x38,0xff,0xff,0xf1,0xff,0xff,0xf0,0xff,0xff,0xff,0xff,0xff,0xff,
	0xff,0xff,0xff,0xff,0xff,0xfe,0x1c,0x30,0xff,0x8c,0x71,0xff,0xff,0xf0,0xff,0xff,0xff,0xff,0xff,0xff,
	0xff,0xff,0xff,0xff,0xff,0xfe,0x1c,0x30,0xff,0x0c,0x31,0xff,0xff,0xf8,0x7f,0xff,0xff,0xff,0xff,0xff,
	0xff,0xff,0xff,0xff,0xff,0xfc,0x38,0x70,0xff,0x0e,0x79,0xff,0xfe,0x38,0x7f,0xff,0xff,0xff,0xff,0xff,
	0xff,0xff,0xff,0xff,0xff,0xfc,0x38,0x71,0xff,0x0f,0xff,0xff,0xce,0x1c,0x3f,0xff,0xff,0xff,0xff,0xff,
	0xff,0xff,0xff,0xff,0xff,0xfe,0x78,0x61,0xff,0x0f,0xff,0xff,0x8e,0x1c,0x7f,0xff,0xff,0xff,0xff,0xff,
	0xff,0xff,0xff,0xff,0xff,0xff,0xf0,0xe1,0xff,0x9f,0xff,0xff,0x87,0x1f,0xff,0xff,0xff,0xff,0xff,0xff,
	0xff,0xff,0xff,0xff,0xff,0xff,0xf8,0xe1,0xff,0xff,0xff,0xff,0x87,0x1f,0xff,0xff,0xff,0xff,0xff,0xff,
	0xff,0xff,0xff,0xff,0xff,0xff,0xff,0xe3,0xff,0xff,0xff,0xff,0x87,0xff,0xff,0xff,0xff,0xff,0xff,0xff,
	0xff,0xff,0xff,0xff,0xff,0xff,0xff,0xe3,0xff,0xff,0xff,0xff,0xc7,0xff,0xff,0xff,0xff,0xff,0xff,0xff,
	0xff,0xff,0xff,0xff,0xff,0xff,0xff,0xff,0xff,0xff,0xff,0xff,0xff,0xff,0xff,0xff,0xff,0xff,0xff,0xff,
	0xff,0xff,0xff,0xff,0xff,0xff,0xff,0xff,0xff,0xff,0xff,0xff,0xff,0xff,0xff,0xff,0xff,0xff,0xff,0xff,
	0xff,0xff,0xff,0xff,0xff,0xff,0xff,0xff,0xff,0xff,0xff,0xff,0xff,0xff,0xff,0xff,0xff,0xff,0xff,0xff,
	0xff,0xff,0xff,0xff,0xff,0xff,0xff,0xff,0xff,0xff,0xff,0xff,0xff,0xff,0xff,0xff,0xff,0xff,0xff,0xff,
	0xff,0xff,0xff,0xff,0xff,0xff,0xff,0xff,0xff,0xff,0xff,0xff,0xff,0xff,0xff,0xff,0xff,0xff,0xff,0xff,
	0xff,0xff,0xff,0xff,0xff,0xff,0xff,0xff,0xff,0xff,0xff,0xff,0xff,0xff,0xff,0xff,0xff,0xff,0xff,0xff
]

def get_token(url):
	values = {
		"device_sn":"862167051501041"
	}
	req = requests.post(url, params=values)
	print(req.status_code)
	print("len={}".format(len(req.content)))
	if len(req.content) == 1762:
		'''
		count = 0
		m = ""
		for i in req.content:
			#print("{},{}".format((binascii.hexlify(bytes(i, encoding="utf-8"))), count))
			s = "{}".format(hex(i))
			if (len(s) == 3):
				s = "0{}".format(s)
			m += " " + s
			count += 1
			if count  == 20:
				count = 0
				m += "\r\n"
		print(m)
		'''
		show_array1762(req.content)

def show_array1762(content):
	try:
		imagebuff = []
		count = 0 
		bit = 0 
		src = []
		for i in content:
			src.append(i)
		for i in range(160):
			for j in range(160):
				radio = math.sqrt(((i - 80)*(i - 80)) + ((j - 80)*(j - 80)))
				if (radio >= 40) and (radio <= 78):
					val = (src[count] & (1 << (7 - (bit % 8))))
					if val > 0:
						show_2vcode_image[(i * 20) + int(j / 8)] |= (1 << (7 - (j % 8)))
					else:
						show_2vcode_image[(i * 20) + int(j / 8)] &= ~(1 << (7 - (j % 8)))
					bit += 1
					if (bit % 8 == 0): 
						count += 1
	except Exception as e:
		print("show_array1762 one error:{}".format(e))
#把160x20的数组转换为160x160的数组送给显示模块
	try:
		print("imagedata len = {}".format(len(show_2vcode_image)))
		for i in range(160):
			line = [0xf] * 160 
			for j in range(20):
				for m in range(8):
					val = show_2vcode_image[i * 20 + j] & (1 << (7 - m)) 
					if val > 0:
						line[160 - (j * 8) - m - 1] = 0
			imagebuff.append(line)
		print_imagebuffer(imagebuff)
		return True
	except Exception as e:
		print("show_array1762 two error:{}".format(e))

def show_array3200(content):
	try:
		imagebuff = []
		for i in range(160):
			line = [0xf] * 160
			for j in range(20):
				for m in range(8):
					val = show_2vcode_image[i * 20 + j] & (1 << (7 - m))
					if val > 0:
						line[160 - (j * 8) - m - 1] = 0
			imagebuff.append(line)
		print_imagebuffer(imagebuff)
	except Exception as e:
		print("show_array3200 error:{}".format(e))

def print_imagebuffer(imagebuff):
#print(imagebuff)
#	print(len(imagebuff))
	s = ""
	for i in range(160):
		for j in range(160):
			if imagebuff[i][j] > 0:
				s += '1'
			else:
				s += '0'
		s += "\r\n"
	print(s)


if __name__ == "__main__":
	token = get_token(url)
#show_array3200(show_2vcode_image)
