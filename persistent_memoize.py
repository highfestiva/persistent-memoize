#!/usr/bin/env python3

from collections import OrderedDict
from functools import partial
from os.path import isdir, join as pathjoin
from threading import Thread


def average_extrapolation(default):
	def extrapolate(prev_values):
		if prev_values:
			return sum(prev_values)/len(prev_values)
		return default
	return extrapolate


def persistent_background_memoize(filename, extrapolate=average_extrapolation(default=0), max_entries=1000):
	'''Memoization that will return an extrapolated (or default) value while a background
	   thread fetches a new one. The values are persistent to <filename> on disk, so the
	   memoization will just keep running when the app is restarted.'''
	def decorator(func):
		class pdict(OrderedDict):
			def __init__(self, filename, func):
				if isdir(filename):
					filename = pathjoin(filename, 'memoize_'+func.__name__)
				self.filename = filename
				self.load()
				self.func = func
				self.background_threads = {}
			def load(self):
				try:
					d = eval(open(self.filename).read())
					self.update(d)
				except FileNotFoundError:
					pass
			def fetch(self, key):
				try:
					value = self[key] = self.func(*key)
					remove_entries = len(self)-max_entries
					if remove_entries >= 10:
						for k in list(self.keys())[:remove_entries]:
							del self[k]
					open(self.filename, 'w').write(repr(self).replace('pdict','OrderedDict'))
					return value
				finally:
					if key in self.background_threads:
						del self.background_threads[key]
			def __call__(self, *args):
				return self[args]
			def __missing__(self, key):
				if not extrapolate:
					return self.fetch(key)
				elif key not in self.background_threads:
					self.background_threads[key] = Thread(target=self.fetch, args=(key,))
					self.background_threads[key].start()
				return extrapolate(self.values())
		return pdict(filename, func)
	return partial(decorator)


def persistent_memoize(filename):
	'''Memoization running only in the foregreound. Will not create worker threads.'''
	return persistent_background_memoize(filename, extrapolate=None)
