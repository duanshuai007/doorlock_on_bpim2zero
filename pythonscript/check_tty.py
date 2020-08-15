#!/usr/bin/env python3
#-*- coding:utf-8 -*-

import sys
import checkserial

if __name__ == "__main__":
	if len(sys.argv) < 2:
		print("paramters error")
		exit(1)
	pid = int(sys.argv[1])
	s = checkserial.checkserial(pid)
	if s.open_serial() == True:
		s.start_thread()
