#!/usr/bin/env python3

from collections import OrderedDict
from functools import partial
from os.path import isdir, join as pathjoin
from random import random
from threading import Thread
from time import sleep, time
from sys import platform


default_path = '/tmp/' if not 'win' in platform else '.'
default_cache_timeout = 60


def average_extrapolation(default):
	def extrapolate(prev_values):
		if prev_values:
			return type(next(iter(prev_values)))(sum(prev_values)/len(prev_values))
		return default
	return extrapolate


def persistent_background_memoize(filename=default_path, extrapolate=average_extrapolation(default=0), max_entries=10000, write_behind_count=0, max_threads=10):
	'''Memoization that will return an extrapolated (or default) value while a background
	   thread fetches a new one. The values are persistent to <filename> on disk, so the
	   memoization will just keep running when the app is restarted.'''
	def decorator(func):
		class pdict(OrderedDict):
			def __init__(self, func, filename):
				super(pdict, self).__init__()
				if isdir(filename):
					filename = pathjoin(filename, 'memoize_'+func.__name__).replace('\\','/')
				self.filename = filename
				self.load()
				self.func = func
				self.background_threads = {}
				self.updates = 0
			def load(self):
				try:
					with open(self.filename) as f:
						d = eval(f.read())
						self.update(d)
				except:
					pass	# Silently pass. All values will have to be reloaded.
			def save(self):
				with open(self.filename, 'w') as f:
					f.write(repr(self).replace('pdict','OrderedDict'))
					self.updates = 0
			def fetch(self, key):
				try:
					value = self[key] = self.func(*key)
					remove_entries = len(self)-max_entries
					self.updates += 1
					if remove_entries >= 10:
						self.updates += remove_entries
						try: # Fixes thread clash at gil release upon checkinterval.
							for k in list(self.keys())[:remove_entries]:
								del self[k]
						except KeyError:
							pass
					if self.updates >= write_behind_count:
						try:
							self.save()
						except:
							pass	# Silently pass. Next thread will write instead.
					return value
				finally:
					if key in self.background_threads:
						del self.background_threads[key]
			def join(self):
				while self.background_threads:
					for thread in self.background_threads.values():
						thread.join()
						break
			def __call__(self, *args):
				return self[args]
			def __missing__(self, key):
				if not extrapolate or max_threads<=0:
					return self.fetch(key)
				elif key not in self.background_threads:
					while len(self.background_threads) > max_threads:
						sleep(random()*0.01)
					if key not in self.background_threads:
						self.background_threads[key] = Thread(target=self.fetch, args=(key,))
						self.background_threads[key].start()
				return extrapolate(self.values())
		fname = default_path if callable(filename) else filename
		return pdict(func, fname)
	if callable(filename):
		func = filename
		return decorator(func)
	else:
		return partial(decorator)


def persistent_memoize(filename='/tmp/', max_entries=10000, write_behind_count=0):
	'''Memoization running only in the foregreound. Will not create worker threads.'''
	return persistent_background_memoize(filename, extrapolate=None, max_entries=max_entries, write_behind_count=write_behind_count)


def cache_memoize(timeout=default_cache_timeout):
	'''Simple, unpersisted caching which flushes old values after N seconds.'''
	def decorator(func):
		class cdict(OrderedDict):
			def __init__(self, func, timeout):
				super(cdict, self).__init__()
				self.func = func
				self.timeout = timeout
			def __call__(self, *args):
				now = time()
				for k,tv in list(self.items()):
					value,t = tv
					if now-t > self.timeout:
						del self[k]
					break # OrderedDict = sorted = no more timeouts left in cache.
				return self[args][0]
			def __missing__(self, key):
				value = self.func(*key)
				t = time()
				self[key] = value,t
				return value,t
		tout = default_cache_timeout if callable(timeout) else timeout
		return cdict(func, tout)
	if callable(timeout):
		func = timeout
		return decorator(func)
	else:
		return partial(decorator)
