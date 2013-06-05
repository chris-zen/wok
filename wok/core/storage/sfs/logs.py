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

import os.path
import sqlite3
#import time
from datetime import datetime

from wok.core.utils.sql import BatchInsert

_LOG_LEVEL_ID = {
	"debug" : 1,
	"info" : 2,
	"warn" : 3,
	"error" : 4
}

_LOG_LEVEL_NAME = {
	0 : None,
	1 : "debug",
	2 : "info",
	3 : "warn",
	4 : "error"
}

class SfsLogs(object):
	def __init__(self, storage):
		self._storage = storage

	def __create_db(self, logs_file):
		conn = sqlite3.connect(logs_file)
		c = conn.cursor()
		c.execute("""
		CREATE TABLE logs (
			timestamp	TEXT,
			level		INTEGER,
			name		TEXT,
			msg			TEXT
		)""")
		return conn

	def __logs_file(self, instance_name, module_id, task_index):
		logs_path = self._storage.module_path(instance_name, module_id)
		logs_name = "{}.logs".format(self._storage.task_prefix(task_index))
		return os.path.join(logs_path, logs_name)

	def __open_conn(self, instance_name, module_id, task_index):
		logs_url = self.__logs_file(instance_name, module_id, task_index)
		if not os.path.exists(logs_url):
			conn = self.__create_db(logs_url)
		else:
			conn = sqlite3.connect(logs_url)
		return conn

	def exist(self, instance_name, module_id, task_index):
		return os.path.exists(self.__logs_file(instance_name, module_id, task_index))

	def append(self, instance_name, module_id, task_index, logs):
		conn = self.__open_conn(instance_name, module_id, task_index)
		cur = conn.cursor()
		bi = BatchInsert(cur, "logs", ["timestamp", "level", "name", "msg"], batch_size = 1)
		for log in logs:
			timestamp = None
			if log[0] is not None:
			#	timestamp = time.mktime(log[0].timetuple()) + 1e-6 * log[0].microsecond
				timestamp = log[0].strftime("%Y%m%d %H%M%S %f")
			level = _LOG_LEVEL_ID.get(log[1], 0)
			bi.insert(timestamp, level, log[2], log[3])
		bi.close()
		conn.commit()
		cur.close()
		conn.close()

	def query(self, instance_name, module_id, task_index):
		conn = self.__open_conn(instance_name, module_id, task_index)
		cur = conn.cursor()

		logs = []

		sql = ["SELECT * FROM logs"]

		cur.execute(" ".join(sql))

		log = cur.fetchone()
		while log is not None:
			timestamp = datetime.strptime(log[0], "%Y%m%d %H%M%S %f")
			ms = timestamp.microsecond / 1000
			timestamp = timestamp.strftime("%Y-%m-%d %H:%M:%S:" + "{0:03}".format(ms))
			level = _LOG_LEVEL_NAME[log[1]].upper()
			logs += [(timestamp, level, log[2], log[3])]
			log = cur.fetchone()
		
		cur.close()
		conn.close()
		return logs