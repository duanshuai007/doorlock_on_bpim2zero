# !/usr/bin/python3
# -*- coding: utf-8 -*-
# @Time    : 2018-06-26 9:10
# @Author  : Jackadam
# @Email   :jackadam@sina.com
# @File    : logging_conf.py
# @Software: PyCharm

import logging.config, logging, os
import time
import os

import config

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DEBUG = True  # 标记是否在开发环境
LOGGERNAME = "acs"

LOGFILE = config.config("/root/config.ini").get("CONFIG", "LOGFILE")
if not os.path.exists(LOGFILE):
	r=os.path.split(LOGFILE)
	if not os.path.exists(r[0]):
		os.makedirs(r[0])

# 给过滤器使用的判断
class RequireDebugTrue(logging.Filter):
	# 实现filter方法
	def filter(self, record):
		return DEBUG

LOGGING = { 
	# 基本设置
	'version': 1,  # 日志级别
	'disable_existing_loggers': False,  # 是否禁用现有的记录器

	# 日志格式集合
	'formatters': {
		# 标准输出格式
		'standard': {
			# [具体时间][线程名:线程ID][日志名字:日志级别名称(日志级别ID)] [输出的模块:输出的函数]:日志内容
			#'format': '[%(asctime)s][%(threadName)s:%(thread)d][%(name)s:%(levelname)s(%(lineno)d)][%(module)s:%(funcName)s]:%(message)s'
			'format': '\033[1;36m[%(asctime)s][%(name)s][%(filename)s(%(lineno)d)][%(levelname)s]\033[0m:%(message)s'
		}   
	}, 
	# 过滤器
	'filters': {
		'require_debug_true': {
			'()': RequireDebugTrue,
		}   
	},  

	# 处理器集合
	'handlers': {
		# 输出到控制台
		'console': {
			'level': 'DEBUG',  # 输出信息的最低级别
			'class': 'logging.StreamHandler',
			'formatter': 'standard',  # 使用standard格式
			'filters': ['require_debug_true', ],  # 仅当 DEBUG = True 该处理器才生效
		},  
	# 输出到文件
		'log': {
			'level': 'DEBUG',
			'class': 'logging.handlers.RotatingFileHandler',
			'formatter': 'standard',
#'filename': os.path.join(BASE_DIR, 'debug.log'),  # 输出位置
			'filename': LOGFILE,  # 输出位置
			'maxBytes': 1024 * 1024 * 1,  # 文件大小 5M
			'backupCount': 10,  # 备份份数
			'encoding': 'utf8',  # 文件编码
		},  
	},  

	# 日志管理器集合
	'loggers': {
		# 管理器
		'default': {
			'handlers': ['console', 'log'],
			'level': 'DEBUG',
			'propagate': True,  # 是否传递给父记录器
		},
		# 管理器
		LOGGERNAME : {
			'handlers': ['console', 'log'],
			'level': 'DEBUG',
			'propagate': False,  # 是否传递给父记录器,也就是传送给root logger,如果设置为True则在console会输出重复的信息
		},
	}
}

class LoggingConsumer():
	def __init__(self):
		logging.config.dictConfig(LOGGING)

class LoggingProducer():
	def __init__(self):
		#root handler 
		'''
		handler = logging.handlers.QueueHandler(logQueue)
		root = logging.getLogger()
		root.addHandler(handler)
		root.setLevel(logging.DEBUG)
		print("root logger:")
		print(root)
		'''
		self.logger = logging.getLogger(LOGGERNAME)
		self.logger.setLevel(logging.DEBUG)
		#print(self.logger)
		pass

	def getlogger(self):
		return self.logger

'''
def log_main():
	# 加载前面的标准配置
	logging.config.dictConfig(LOGGING)

	# 获取loggers其中的一个日志管理器
	logger = logging.getLogger("shoujitiku")
	return logger

loger = log_main()
loger.debug('hello')
'''
