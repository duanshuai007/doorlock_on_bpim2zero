#!/usr/bin/env python3
#-*- coding:utf-8 -*-


l1 = [1,2,3,4]
l2 = [5,6,7,8]
l3 = [9,10,11,12]
l4 = [13,13,14,16]
l5 = [1,2,3,4]
ll = [l1, l2, l3, l4, l5]
#print(bytes(l1))
print("ll={}".format(ll))
#ln = [bytes(l1), bytes(l2), bytes(l3)]
#print(ln)

b = bytes() 
for l in ll:
	b += bytes(l)
#b1 = bytes(l1)
#b2 = bytes(l2)
#b3 = b1 + b2
#print("b1={}, b2={}, b3={}".format(b1, b2, b3))
print(b)
