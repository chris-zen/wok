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

from threading import Lock

def synchronized(f):
	"""Synchronization decorator for methods of Synchronizable objects"""

	def wrap(f):
		def sync_function(obj, *args, **kw):
			#log.debug("<ACQUIRE %s>" % f.__name__)
			obj._acquire()
			try:
				return f(obj, *args, ** kw)
			finally:
				try:
					#log.debug("<RELEASE %s>" % f.__name__)
					obj._release()
				except:
					from wok.logger import get_logger
					get_logger(name = "synchronized").error(
						"<RELEASE ERROR %s.%s>" % (
							obj.__class__.__name__, f.__name__))
		return sync_function
	return wrap(f)

class Synchronizable(object):
	"""An object that can have methods decorated with @synchronized"""

	def __init__(self, lock = None):
		if lock is None:
			lock = Lock()
			
		self._lock = lock

	def _acquire(self):
		self._lock.acquire()

	def _release(self):
		self._lock.release()