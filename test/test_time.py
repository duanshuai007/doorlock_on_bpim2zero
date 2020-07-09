import time
import random

print(int(time.time()))

print(int(time.time() * 100))

r = random.randint(100000, 999999)
print(r)

print(time.localtime())
print(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()))


t = time.localtime(1593975518)
dt = time.strftime("%Y-%m-%d %H:%M:%S", t)
print(dt)

t1 = 1593975518
t2 = 1593975523

print(abs(t1 - t2))
print(abs(t2 - t1))
