#!/usr/bin/env python3
#-*- coding:utf-8 -*-

import sys
import os

import message_struct as ms

def gzip_uncompress_with_password(gzfile:str, tardir:str)->None:
	if not os.path.exists(gzfile):
		print("not find gzfile")
		return
	if not os.path.exists(tardir):
		print("not find tardir")
		return

	salt = ms.DOORSTONE
	cmd = "dd if={} | openssl des3 -d -k {}{}{} | tar zxvf - -C{} > /dev/null".format(gzfile, "\\\"", salt, "\\\"", tardir)
	os.system(cmd)

if __name__ == '__main__':
	if len(sys.argv) < 3:
		print("must have gzfile and tardir paramters")
		exit(1)
	gzfile = sys.argv[1]
	tardir = sys.argv[2]
	gzip_uncompress_with_password(gzfile, tardir)

