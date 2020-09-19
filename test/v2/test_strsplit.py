
teststr="3,0;4,0;"

ret=teststr.split(';')
print(ret)
for v in ret:
	if len(v) == 0:
		continue
	print(v)
	t = v.split(',')
	print(t)
