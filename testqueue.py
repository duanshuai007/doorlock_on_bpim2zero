import queue

l = ['a', 'b', 'c', 'd']

print(l)
l.remove('c')

print(l)

l = [{"key":1, "msg":"hello"}, {"key":2, "msg":"world"}, {"key":3, "msg":"wowo"}]

print(l)
for i in l:
	if i["key"] == 2:
		l.remove(i)

print(l)
