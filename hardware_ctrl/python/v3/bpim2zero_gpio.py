#!/usr/bin/env python3
#-*- coding:utf-8 -*-

import mmap
import struct

class GPIO:
	#-------------------------------------------------------------------------------------#
	#定义GPIO相对0x01C20000的偏移地址
	BASE_ADDR = 0x01C20000
	PIO_OFFSET = 0x800

	PA_INT_CFG0 = 0x200 + 0 * 0x20 + 0x00
	PA_INT_CFG1 = 0x200 + 0 * 0x20 + 0x04
	PA_INT_CFG2 = 0x200 + 0 * 0x20 + 0x08
	PA_INT_CFG3 = 0x200 + 0 * 0x20 + 0x0C
	PA_INT_CTL  = 0x200 + 0 * 0x20 + 0x10
	PA_INT_STA  = 0x200 + 0 * 0x20 + 0x14
	PA_INT_DEB  = 0x200 + 0 * 0x20 + 0x18
	PG_INT_CFG0 = 0x200 + 1 * 0x20 + 0x00
	PG_INT_CFG1 = 0x200 + 1 * 0x20 + 0x04
	PG_INT_CFG2 = 0x200 + 1 * 0x20 + 0x08
	PG_INT_CFG3 = 0x200 + 1 * 0x20 + 0x0C
	PG_INT_CTL  = 0x200 + 1 * 0x20 + 0x10
	PG_INT_STA  = 0x200 + 1 * 0x20 + 0x14
	PG_INT_DEB  = 0x200 + 1 * 0x20 + 0x18

	PIO_MEM_SIZE = 0x400 * 4

	gpio_common_func_dict = {
		"input"		: 0,
		"output"	: 1,
		"disable"	: 7,
	}

	gpio_register_dict = {
		"pinbits" : 4,	#每一个引脚功能配置所需要的位数
		"gpioa" : {
			"cfg0" : 0 * 0x24 + 0x00,
			"cfg1" : 0 * 0x24 + 0x04,
			"cfg2" : 0 * 0x24 + 0x08,
			"cfg3" : 0 * 0x24 + 0x0C,
			"dat"  : 0 * 0x24 + 0x10,
			"drv0" : 0 * 0x24 + 0x14,
			"drv1" : 0 * 0x24 + 0x18,
			"pul0" : 0 * 0x24 + 0x1C,
			"pul1" : 0 * 0x24 + 0x20,
			"total" : 22,
			"pin7cfg" : {
				"input"		: 0,
				"output"	: 1,
				"sim_clk"	: 2,
				"pa_eint7"	: 6,
				"io_disable": 7,
			}
		},
		"gpioc" : {
			"cfg0" : 1 * 0x24 + 0x00,
			"cfg1" : 1 * 0x24 + 0x04,
			"cfg2" : 1 * 0x24 + 0x08,
			"cfg3" : 1 * 0x24 + 0x0C,
			"dat"  : 1 * 0x24 + 0x10,
			"drv0" : 1 * 0x24 + 0x14,
			"drv1" : 1 * 0x24 + 0x18,
			"pul0" : 1 * 0x24 + 0x1C,
			"pul1" : 1 * 0x24 + 0x20,
			"total" : 19,
		},
		"gpiod" : {
			"cfg0" : 2 * 0x24 + 0x00,
			"cfg1" : 2 * 0x24 + 0x04,
			"cfg2" : 2 * 0x24 + 0x08,
			"cfg3" : 2 * 0x24 + 0x0C,
			"dat"  : 2 * 0x24 + 0x10,
			"drv0" : 2 * 0x24 + 0x14,
			"drv1" : 2 * 0x24 + 0x18,
			"pul0" : 2 * 0x24 + 0x1C,
			"pul1" : 2 * 0x24 + 0x20,
			"total" : 18,
		},
		"gpioe" : {
			"cfg0" : 3 * 0x24 + 0x00,
			"cfg1" : 3 * 0x24 + 0x04,
			"cfg2" : 3 * 0x24 + 0x08,
			"cfg3" : 3 * 0x24 + 0x0C,
			"dat"  : 3 * 0x24 + 0x10,
			"drv0" : 3 * 0x24 + 0x14,
			"drv1" : 3 * 0x24 + 0x18,
			"pul0" : 3 * 0x24 + 0x1C,
			"pul1" : 3 * 0x24 + 0x20,
			"total" : 16,
		},
		"gpiof" : {
			"cfg0" : 4 * 0x24 + 0x00,
			"cfg1" : 4 * 0x24 + 0x04,
			"cfg2" : 4 * 0x24 + 0x08,
			"cfg3" : 4 * 0x24 + 0x0C,
			"dat"  : 4 * 0x24 + 0x10,
			"drv0" : 4 * 0x24 + 0x14,
			"drv1" : 4 * 0x24 + 0x18,
			"pul0" : 4 * 0x24 + 0x1C,
			"pul1" : 4 * 0x24 + 0x20,
			"total" : 7,
		},
		"gpiog" : {
			"cfg0" : 5 * 0x24 + 0x00,
			"cfg1" : 5 * 0x24 + 0x04,
			"cfg2" : 5 * 0x24 + 0x08,
			"cfg3" : 5 * 0x24 + 0x0C,
			"dat"  : 5 * 0x24 + 0x10,
			"drv0" : 5 * 0x24 + 0x14,
			"drv1" : 5 * 0x24 + 0x18,
			"pul0" : 5 * 0x24 + 0x1C,
			"pul1" : 5 * 0x24 + 0x20,
			"total" : 14,
		},
	}

	cfgname_list = ["cfg0", "cfg1", "cfg2", "cfg3"]
	#-------------------------------------------------------------------------------------#
	#以下是构造函数和析构函数
	def __init__(self):
		self.m_mmap = None
		self.fd = None
		"""
		GPIO初始化函数
		函数会打开/dev/mem文件，并映射从0x01C20000地址开始，共8192字节长度（2页）的内存空间到用户的虚拟地址
		返回值：无
		"""
		self.fd = open("/dev/mem", "rb+")
		#print("self.PIO_MEM_SIZE = {}, self.BASE_ADDR={}".format(self.PIO_MEM_SIZE, self.BASE_ADDR))
		self.m_mmap = mmap.mmap(self.fd.fileno(), self.PIO_MEM_SIZE, mmap.MAP_SHARED, mmap.PROT_WRITE | mmap.PROT_READ, mmap.ACCESS_WRITE, self.BASE_ADDR)
		assert self.m_mmap != None,"Init Fails"

	def __del__(self):
		if self.m_mmap is not None:
			self.m_mmap.close()
		if self.fd is not None:
			self.fd.close()

	def setPinFunc(self, gpio:str, pin:int, func:str)->None:
		assert gpio in self.gpio_register_dict.keys(), "{} not exists".format(gpio)
		assert 0 < pin < self.gpio_register_dict[gpio]["total"] , "pin value too big"
		assert func is not None, "func can't None"

		#print(self.gpio_register_dict.keys())
		#addr = self.gpio_register_dict[gpio]["base"] + self.PIO_OFFSET
		offset = int(pin / 8)
		#realaddr = addr + offset * 0x04
		realaddr = self.gpio_register_dict[gpio][self.cfgname_list[offset]] + self.PIO_OFFSET
		#print("offset={} realaddr={}".format(offset, hex(realaddr)))
		self.m_mmap.seek(realaddr)
		conf = self.m_mmap.read(4)
		byte_conf = struct.unpack('L', conf)[0]
		offset = pin % 8
		#print("old conf={} offset={}".format(hex(byte_conf), offset))
		byte_conf &= ~(7 << (offset * self.gpio_register_dict["pinbits"]))
		byte_conf |= self.gpio_common_func_dict[func] << (offset * self.gpio_register_dict["pinbits"])
		#print("new conf = {}".format(hex(byte_conf)))
		conf = struct.pack('L', byte_conf)
		self.m_mmap.seek(realaddr)
		self.m_mmap.write(conf)

	def readPin(self, gpio:str, pin:int)->int:
		assert gpio in self.gpio_register_dict.keys(), "{} not exists".format(gpio)
		assert 0 < pin < self.gpio_register_dict[gpio]["total"] , "pin value too big"
		
		realaddr = self.gpio_register_dict[gpio]["dat"] + self.PIO_OFFSET
		
		self.m_mmap.seek(realaddr)
		val = self.m_mmap.read(4)
		byte_val = struct.unpack('L', val)[0]
		
		return (byte_val >> pin) & 1;
		pass

	def writePin(self, gpio:str, pin:int, val:int)->None:
		assert gpio in self.gpio_register_dict.keys(), "{} not exists".format(gpio)
		assert 0 < pin < self.gpio_register_dict[gpio]["total"] , "pin value too big"
		
		realaddr = self.gpio_register_dict[gpio]["dat"] + self.PIO_OFFSET
	
		self.m_mmap.seek(realaddr)
		origin_val = self.m_mmap.read(4)
		byte_val = struct.unpack('L', origin_val)[0]

		#print("old val:{}".format(hex(byte_val)))
		if val == 1:
			byte_val |= (1 << pin)
		else:
			byte_val &= ~(1 << pin)

		#print("new val:{}".format(hex(byte_val)))
		self.m_mmap.seek(realaddr)
		newval = struct.pack('L', byte_val)
		self.m_mmap.write(newval)
		pass

	def readGPIO(self, gpio:str)->int:
		assert gpio in self.gpio_register_dict.keys(), "{} not exists".format(gpio)
		realaddr = self.gpio_register_dict[gpio]["dat"] + self.PIO_OFFSET
		self.m_mmap.seek(realaddr)
		val = self.m_mmap.read(4)
		byte_val = struct.unpack('L', val)[0]
		return byte_val;

	def writeGPIO(self, gpio:str, val:int)->None:
		realaddr = self.gpio_register_dict[gpio]["dat"] + self.PIO_OFFSET
		self.m_mmap.seek(realaddr)
		newval = struct.pack('L', val)
		self.m_mmap.write(newval)
		pass

	#-------------------------------------------------------------------------------------#
	#以下是成员函数
	def ReadGPIO(self, gpio:str)->int:
		"""
		读取一个寄存器的值
		reg_addr:要读取的寄存器地址（必须为4的倍数），且范围在2个pagesize内，即小于8192
		返回值：寄存器的值（4字节）
		"""
		assert self.m_mmap != None,"Init Fails"
		self.m_mmap.seek(reg_addr)
		ReadBytes = self.m_mmap.read(4)
		#print("read:{}".format(ReadBytes))
		return struct.unpack('L',ReadBytes)[0]

	def WriteReg(self, gpio:str, value:int)->int:
		"""
		写一个寄存器的值
		reg_addr:要写入的寄存器地址（必须为4的倍数），且范围在2个pagesize内，即小于8192
		value:要写入的值，整形，一次写入四个字节长度的整数，即0xffffffff
		返回值：无
		"""     
		assert self.m_mmap != None,"Init Fails"
		assert reg_addr % 4 == 0,"reg_addr must be mutiple of 4"
		assert 0 <= reg_addr <= 8192,"reg_addr must be less than 8192,which is 2 pagesize"
		assert 0 <= value <= 0xFFFFFFFF,"value must be less than 0xFFFFFFFF,which is 4 bytes"

		self.m_mmap.seek(reg_addr)
		BytesToWrite = struct.pack('L',value)
		#print("write:{}".format(BytesToWrite))
		self.m_mmap.write(BytesToWrite)
		return
