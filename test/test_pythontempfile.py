#!/usr/bin/env python3
#-*- coding:utf-8 -*-

import os
from tempfile import TemporaryFile

def test():
	f = TemporaryFile()
	f.seek(0)
	bytemsg = bytes("dasjdjsalkflkdsklfdsalhfldshalfhskadhfhdsfhdsalfhdlska", encoding='utf-8')
	f.write(bytemsg)
	print(len(bytemsg))

	f.seek(0)
	s = f.read(1024)
	strmsg = str(s, encoding='utf-8')
	print(strmsg)
	print(s)


if __name__ == "__main__":
	test()
