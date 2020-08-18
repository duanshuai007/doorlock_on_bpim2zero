#!/usr/bin/env python3


import watchdog


def test_func():
	watchdog.set_timeout(60)
	r = watchdog.get_timeout()
	print(r)
	s = watchdog.get_bootstatus()
	print(s)
	watchdog.feed()
	watchdog.stop()
	pass


if __name__ == "__main__":
	test_func()
