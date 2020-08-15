#!/usr/bin/env python
# -*- coding:utf-8 -*-
from distutils.core import setup,Extension
from Cython.Build import cythonize

setup(	
		name='python_modules',
		version='1.0',
		platforms='arm',
		description='doorlock python modules',
		author='bigfish',
		author_email='duanbixing@163.com',
		ext_modules=cythonize([	
			"watchdog/watchdog.c", 
			"config/config.py", 
			"message_struct/message_struct.py",
			"logger/LoggingQueue.py",
			"mqtt/mqtt.py",
			"spilcd/spilcd_api.c",
			"wx2vcode/wx2vcode.py",
			"generate_pillow_buffer/generate_pillow_buffer.py",
			"downloadfile/downloadfile.py",
			"checkfiletype/checkfiletype.py",
			"uncompressfirmware/uncompressfirmware.py",
			"checkserial/checkserial.py"
		])
	  )

#setup(	
#		name='python_modules',
#		version='1.0',
#		description='doorlock python modules',
#		ext_modules=[
#			Extension(	name='python_moduls',
#						sources=["watchdog/watchdog.c"],
#						extra_compile_args=['--march=arm'])
#			],
#	  )
