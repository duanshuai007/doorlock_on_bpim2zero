import os
import sys
import time

print(int(time.time()))
mtime = int(os.stat("./test_timestamp.py").st_mtime)

print(mtime)

print(time.localtime(mtime))
