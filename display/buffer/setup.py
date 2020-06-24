#!/usr/bin/env python
# -*- coding:utf-8 -*-

from distutils.core import setup,Extension

SPILCD_Extension=Extension('spilcd',sources=['buffer.c'])

setup(name='spilcd',
		version='1.0',
		description='spilcd driver by c',
		ext_modules=[SPILCD_Extension])
