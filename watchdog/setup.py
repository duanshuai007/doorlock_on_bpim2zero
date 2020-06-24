#!/usr/bin/env python
# -*- coding:utf-8 -*-

from distutils.core import setup,Extension

WATCHDOG_Extension=Extension('watchdog',sources=['watchdog.c'])

setup(name='watchdog',
		version='1.0',
		description='watchdog driver by c',
		ext_modules=[WATCHDOG_Extension])
