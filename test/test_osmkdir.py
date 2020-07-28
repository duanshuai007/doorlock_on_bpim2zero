import os

#filepath="/home/swann/workgit/acs/test/log/test/logfile.log"
filepath="/home/download/firmware_16.des3.tar.gz"
if not os.path.exists(filepath):
	r=os.path.split(filepath)
	print(r)
	if not os.path.exists(r[0]):
		os.makedirs(r[0])
