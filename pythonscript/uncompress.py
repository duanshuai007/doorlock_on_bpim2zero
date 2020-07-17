#!/usr/bin/env python3
#-*- coding:utf-8 -*-

import sys
import uncompressfirmware as u

if __name__ == "__main__":
	if len(sys.argv) < 3:
		print("must have gzfile and tardir paramters")
		exit(1)

	gzfile = sys.argv[1]
	tardir = sys.argv[2]
	u.gzip_uncompress_with_password(gzfile, tardir)
