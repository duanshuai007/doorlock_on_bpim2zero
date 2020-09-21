import re

tstr=":3,0;"

t = "(^{};|;{};)".format("3,0", "3,0")
p = re.compile(r'{}'.format(t))
ret = p.findall(tstr)
print(ret)

tstr="3,0;4,2;5,0;14,0;17,0;"
t = "(^{},[0|1|2];|;{},[0|1|2];)".format(3,3)
p = re.compile(r'{}'.format(t))
ret = p.findall(tstr)
print(ret)
if len(ret) != 0:
	if ret[0][0] == ';':
		tstr = tstr.replace(ret[0], ";")
	else:
		tstr = tstr.replace(ret[0], "")
		
print(tstr)

