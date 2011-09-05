# ******************************************************************
# Copyright 2009, Universitat Pompeu Fabra
#
# Licensed under the Non-Profit Open Software License version 3.0
# ******************************************************************

class RunState(object):
	def __init__(self, id, title):
		self.id = id
		self.title = title

	def __eq__(self, other):
		return isinstance(other, RunState) and self.id == other.id

	def __hash__(self):
		return hash(self.id)

	def __str__(self):
		return self.title

	def __repr__(self):
		return "{}({})".format(self.title, self.id)

class UndefinedState(Exception):
	def __init__(self, title):
		Exception.__init__(self, "Undefined state: {}".format(title))


READY = RunState(1, 'ready')
PAUSED = RunState(2, 'paused')
WAITING = RunState(3, 'waiting')
RUNNING = RunState(4, 'running')
FINISHED = RunState(5, 'finished')
FAILED = RunState(6, 'failed')

__STATES = [
	READY, PAUSED, WAITING, RUNNING, FINISHED, FAILED ]

__MAP = {}
for s in __STATES:
	__MAP[s.title] = s

def from_title(title):
	if title not in __MAP:
		raise UndefinedState(title)

	return __MAP[title]