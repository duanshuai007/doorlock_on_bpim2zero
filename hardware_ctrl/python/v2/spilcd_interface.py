#!/usr/bin/env python3
#-*- coding:utf-8 -*-

import time
import spilcd_api

class spilcd_interface():

	CS_ENABLE	= 0
	CS_DISABLE	= 1
	A0_CMD		= 0
	A0_DATA		= 1
	RST_ENABLE	= 0
	RST_DISABLE = 1

	def __init__(self):
		print("spilcd_interface init")
		spilcd_api.on()
		pass

	def ndelay(self, count):
		time.sleep(count / 1000000000)

	def begin_write_data(self):
		spilcd_api.set_cs_low()
		spilcd_api.set_a0_high()
		self.ndelay(200)

	def continue_write_data(self, datalist:list):
		for m in range(160):
			for n in range(81):
				data = datalist[m*81 + n]
				for i in range(8):
					spilcd_api.set_sck_low()
					if (data & 0x80) == 0:
						spilcd_api.set_sda_low()
					else:
						spilcd_api.set_sda_high()
#self.ndelay(10)
					spilcd_api.set_sck_high()
					data <<= 1
#self.ndelay(10)

	def end_write_data(self):
		spilcd_api.set_cs_high()

	def write_cmd(self, cmd):
		spilcd_api.set_cs_low()
		spilcd_api.set_a0_low()
		self.ndelay(220)
		for i in range(8):
			spilcd_api.set_sck_low()
			if (cmd & 0x80) == 0:
				spilcd_api.set_sda_low()
			else:
				spilcd_api.set_sda_high()
			self.ndelay(50)
			spilcd_api.set_sck_high()
			self.ndelay(50)
			cmd <<= 1
		self.ndelay(50)
		spilcd_api.set_a0_high()

	def open_screen(self):
		self.write_cmd(0xa8 | (0 << 2) | (0 << 1) | (1 << 0))
		time.sleep(0.02)

	def close_screen(self):
		self.write_cmd(0xa8 | (0 << 2) | (0 << 1) | (0 << 0))
		time.sleep(0.02)

	
	def lcd_window_init(self, start_row, start_col, width, height)->bool:
		if start_row > 159 or start_row + height > 160:
			return False
		if start_col > 54 or start_col + width > 54:
			return False
		self.write_cmd(0x05)
		self.write_cmd(0x12)
		self.write_cmd(0x60)
		self.write_cmd(0x70)
		
		#设置窗口左边界
		self.write_cmd(0xf4)
		self.write_cmd(start_col + 37)
		#设置窗口上边界	
		self.write_cmd(0xf5)
		self.write_cmd(start_row)
		#设置窗口右边界
		self.write_cmd(0xf6)
		self.write_cmd(start_col + 37 + width)
		#设置窗口下边界
		self.write_cmd(0xf7)
		self.write_cmd(start_row + height)
		return True	

	def lcd_window_enable(self, state:bool):
		if state == True:
			self.write_cmd(0xf8 | 0)
		else:
			self.write_cmd(0xf8 | 1)

	def lcd_init(self)->None:
		#系统初始化
		self.write_cmd(0xe2)
		time.sleep(0.2)
		#设置温度补偿
		self.write_cmd(0x24 | 0)
		#电源控制设置
		#pc0:0->承受lcd负载<=13nF, 1->承受lcd负载为13nF<lcd<=22nF
		#pc1:0->关闭内置升压电路, 1->启用内部升压电路
		self.write_cmd(0x28 | 3)

		#lcd映像设置
		self.write_cmd(0xC0)
		#设置帧率
		self.write_cmd(0xA0 | 2)
		#M信号波形设置
		self.write_cmd(0xC8)
		self.write_cmd(0x0F)
		#显示数据格式设置
		#0: BRGBGRBGR...BGR
		#1: RGBRGBRGB...RGB
		self.write_cmd(0xD0 | 1)

		#RGB数据格式设置
		#增强模式为0(对应0xa8指令中的值), 
		#此处设置为1时: 数据格式:RRRR-GGGGG-BBB，每3个字节存储两组数据
		#R R R R G G G G 
		#G B B B R R R R
		#G G G G G B B B
		#此处设置为2时:数据格式:RRRRR-GGGGGG-BBBBB,可以直接保存在16位ram内
		#R R R R R G G G
		#G G G B B B B B
		self.write_cmd(0xd4 | 1)

		#偏压比设置 取值范围0-3
		self.write_cmd(0xe8 | 1)

		#设置对比度电压 取值范围0-255
		self.write_cmd(0x81)
		self.write_cmd(188)
			
		#设置全显示 0->关闭全显示 1->打开全显示
		#write_cmd(0xa4 | 0)

		#设置负性显示 0关闭 1开启
		self.write_cmd(0xa6 | 0)

		#显示使能设置
		#(0): 1开显示 0关显示
		#(1): 1开启灰度显示 0关闭灰度显示
		#(2): 1关闭增强模式 0开启增强模式
		self.write_cmd(0xa8 | (1<<0) | (0 << 1) | (0 << 2))
		#该指令执行后需要延时10毫秒不操作lcd模块来保证不对模块造成有害的干扰
		time.sleep(0.02)

	def lcd_reset(self):
		self.write_cmd(0xe2)
		time.sleep(0.3)
	
