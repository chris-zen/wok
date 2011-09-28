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