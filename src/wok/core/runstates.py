###############################################################################
#
#    Copyright 2009-2011, Universitat Pompeu Fabra
#
#    This file is part of Wok.
#
#    Wok is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    Wok is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses
#
###############################################################################

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
WAITING = RunState(2, 'waiting')
RUNNING = RunState(3, 'running')
PAUSED = RunState(4, 'paused')
ABORTING = RunState(5, 'aborting')
FINISHED = RunState(6, 'finished')
RETRY = RunState(7, 'retry')
FAILED = RunState(8, 'failed')
ABORTED = RunState(9, 'aborted')

__STATES = [
	READY, WAITING, RUNNING, PAUSED, ABORTING, FINISHED, RETRY, FAILED, ABORTED ]

__MAP = {}
for s in __STATES:
	__MAP[s.title] = s

def from_title(title):
	if title not in __MAP:
		raise UndefinedState(title)

	return __MAP[title]