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
			"watchdog.c", 
		])  
)  
