import os

filepath="/home/swann/workgit/acs/test/log/test/logfile.log"
if not os.path.exists(filepath):
	r=os.path.split(filepath)
	if not os.path.exists(r[0]):
		os.makedirs(r[0])
