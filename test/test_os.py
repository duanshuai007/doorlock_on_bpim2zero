#!/usr/bin/env python3
#-*- coding:utf-8 -*-

import os

cmd = "ps -ef"
ret = os.system(cmd)
print("ret = {}".format(ret))
