#!/usr/bin/env python3
#-*- coding:utf-8 -*-

import os

#cmd = "ps -ef"
#ret = os.system(cmd)
#print("ret = {}".format(ret))

#out = os.popen("ifconfig | grep 'inet addr:' | grep -v '127.0.0.1' | cut -d: -f2 | awk '{print $1}' | head -1").read()
#ip = out.split('\n')[0]
#print(out)
#print(ip)
current = os.popen("cat ./current_network").read().split('\n')[0]
print(current)
cmd1="ifconfig {} | grep 'inet addr' ".format(current)
cmd2 = "{}{}{}{}".format(" | awk -F\" \" ", "'{", "print $2", "}'")
cmd3 = "{}{}{}{}".format(" | awk -F\":\" ", "'{", "print $2", "}'")
cmd = "{}{}{}".format(cmd1, cmd2, cmd3)

print(cmd)
ret = os.popen(cmd).read().split('\n')[0]
print(ret)

import hashlib

m = hashlib.md5()
with open("./test_os.py", 'r') as f:
	s = f.read(1024)
	print(s)
	m.update(s.encode("utf-8"))
print(m.hexdigest())

print(type(m.hexdigest()))
