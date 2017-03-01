#!/usr/bin/env python3

from persistent_memoize import *


def test_foreground_memoize():
	import os
	if os.path.exists('testdb'):
		os.remove('testdb')
	global callcnt
	callcnt = 0
	@persistent_memoize('testdb', max_entries=100)
	def somecall(t, apa, bepa):
		global callcnt
		callcnt += 1
		return apa*3, bepa*2
	assert somecall(55, 9434, 'xo') == (28302, 'xoxo')
	assert somecall(55, 9434, 'xo') == (28302, 'xoxo') # Use memory caching.
	assert somecall(56, 9434, 'xox') == (28302, 'xoxxox')
	somecall.clear()
	somecall.load()	# Use DB caching.
	assert somecall(56, 9434, 'xox') == (28302, 'xoxxox')
	assert callcnt == 2
	for x in range(200):
		somecall[x] = x
	somecall(57, 'a', 'b')
	assert len(somecall) == 100
	os.remove('testdb')


def test_background_memoize():
	import os
	import time
	if os.path.exists('testdb'):
		os.remove('testdb')
	global callcnt
	callcnt = 0
	@persistent_background_memoize('testdb')
	def othercall(n):
		global callcnt
		callcnt += 1
		time.sleep(0.001)
		return n//11
	assert othercall(55) == 0 # Extrapolation from nothing.
	time.sleep(0.05)
	assert othercall(55) == 5 # Memoized.
	assert othercall(66) == 5 # Extrapolated from previously memoized.
	time.sleep(0.05)
	assert othercall(66) == 6 # Memoized.
	assert callcnt == 2
	for _ in range(10):
		othercall(77)
	othercall.join()
	assert callcnt == 3 # Make sure only one background thread was started.
	assert len(othercall.background_threads) == 0
	os.remove('testdb')


def test_auto_filename():
	import os
	import time
	if os.path.exists('memoize_testdb'):
		os.remove('memoize_testdb')
	@persistent_memoize # Persist using function name in default directory.
	def testdb(i):
		pass
	for i in range(100):
		testdb(i)
	assert os.path.exists('memoize_testdb')
	os.remove('memoize_testdb')


def test_thread_flood():
	import os
	import time
	if os.path.exists('memoize_slow'):
		os.remove('memoize_slow')
	@persistent_background_memoize # Persist using function name in default directory.
	def slow(i):
		time.sleep(0.001)
		return 0
	for i in range(100):
		slow(i)
	slow.join()
	assert os.path.exists('memoize_slow')
	os.remove('memoize_slow')


def test_caching():
	import time
	@cache_memoize
	def slow(i):
		time.sleep(0.001)
		return i
	t = time.time()
	for n in range(1000):
		slow(4)
	assert time.time()-t < 0.1


if __name__ == '__main__':
	test_foreground_memoize()
	test_background_memoize()
	test_auto_filename()
	test_thread_flood()
	test_caching()
	print('Foreground, background, persistence and caching seems ok.')
