#!/usr/bin/env python
# -*- coding:utf-8 -*-

from distutils.core import setup,Extension

SPILCD_Extension=Extension('spilcd_api',sources=['spilcd_api.c'])

setup(name='spilcd_api',
		version='1.0',
		description='spilcd_api driver by c',
		ext_modules=[SPILCD_Extension])
