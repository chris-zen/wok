import os
import os.path
import sqlite3
import threading
import time
from datetime import datetime

from wok.core.sync import Synchronizable, synchronized
from wok.core.utils.sql import BatchInsert

_ALL_CACHES = 0

_LOGS_CACHE = 1

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

class SqliteEngineDB(Synchronizable):
	def __init__(self, engine):
		Synchronizable.__init__(self)
		
		self._engine = engine

		self._base_path = os.path.join(engine.work_path, "db")

		self._global_db_file = os.path.join(self._base_path, "__engine.db")
		self._global_conn = None

		self._instances_conn = {}

		self._conn_cache = {}
		self._conn_cache_thread_del = []

	def __create_global_db(self):
		conn = sqlite3.connect(self._global_db_file)
		#TODO create tables
		return conn

	def __init_global_db(self):
		if not os.path.exists(self._global_db_file):
			self._global_conn = self.__create_global_db()
		else:
			self._global_conn = sqlite3.connect(self._global_db_file)

	def __create_instance_db(self, inst_db_file, instance):
		conn = sqlite3.connect(inst_db_file)
		c = conn.cursor()
		c.execute("""
		CREATE TABLE modules (
			module_id	INTEGER,
			name		TEXT,
			path		TEXT,

			PRIMARY KEY (module_id)
		)""")
		c.execute("""
		CREATE TABLE logs (
			module_id	INTEGER,
			task_index	INTEGER,
			timestamp	TEXT,
			level_id	INTEGER,
			msg			TEXT
		)""")
		conn.commit()
		c.close()
		return conn

	def __open_instance_conn(self, instance):
		if instance.name in self._instances_conn:
			return self._instances_conn[instance.name]

		inst_db_file = os.path.join(self._base_path, "%s.db" % instance.name)

		if os.path.exists(inst_db_file):
			conn = sqlite3.connect(inst_db_file)
		else:
			conn = self.__create_instance_db(inst_db_file, instance)

		self._instances_conn[instance.name] = conn

		return conn

	def __close_instance_conn(self, conn, instance):
		conn.close()
		del self._instances_conn[instance.name]

	def instance_persist(self, instance):
		#conn = self.__open_instance_conn(instance)
		#TODO ...
		#self.__close_instance_conn(conn, instance)
		pass

	def __ensure_path(self, path):
		if not os.path.exists(path):
			try:
				os.makedirs(path)
			except:
				if not os.path.exists(path):
					raise

	def __conn_cache_put(self, cache_id, conn, *key):
		thread_id = threading.current_thread().ident
		key = (cache_id, thread_id) + key
		if key in self._conn_cache:
			prev_conn = self._conn_cache[key][0]
			if prev_conn != conn:
				prev_conn.close()

		if len(self._conn_cache) > 2:
			dk = sorted(self._conn_cache.items(), key=lambda x: x[1][1])[0][0]
			self.__conn_cache_del(*dk)

		self._conn_cache[key] = (conn, datetime.now())

	def __conn_cache_del(self, *key):
		if key[1] == thread_id:
			self._conn_cache[key][0].close()
			del self._conn_cache[key]
		else:
			if thread_id in self._conn_cache_thread_del:
				self._conn_cache_thread_del[thread_id] += [key]
			else:
				self._conn_cache_thread_del[thread_id] = [key]
		
	def __conn_cache_get(self, cache_id, *key):
		thread_id = threading.current_thread().ident
		cache_elm = self._conn_cache.get((cache_id, thread_id,) + key)
		if cache_elm is None:
			return None
		return cache_elm[0]

	def __conn_cache_clean(self, cache_id = _ALL_CACHES):
		thread_id = threading.current_thread().ident
		dkeys = []
		for key in self._conn_cache:
			if (cache_id != _ALL_CACHES and cache_id != key[0]) and key[1] != thread_id:
				continue
			dkeys += [key]

		for key in dkeys:
			self.__conn_cache_del(*key)

	def __create_logs_db(self, logs_file):
		conn = sqlite3.connect(logs_file)
		c = conn.cursor()
		c.execute("""
		CREATE TABLE logs (
			task_index	INTEGER,
			timestamp	TIMESTAMP,
			level		INTEGER,
			name		TEXT,
			msg			TEXT
		)""")
		return conn

	def __open_logs_conn(self, task):
		module = task.parent
		instance = task.parent.instance
		key = (instance.name, module.name)
		conn = self.__conn_cache_get(_LOGS_CACHE, key)
		if conn is not None:
			return conn
		logs_path = os.path.join(self._base_path, instance.name, module.name)
		self.__ensure_path(logs_path)
		logs_file = os.path.join(logs_path, "logs.sqlite")
		if not os.path.exists(logs_file):
			conn = self.__create_logs_db(logs_file)
		else:
			conn = sqlite3.connect(logs_file)
		self.__conn_cache_put(_LOGS_CACHE, conn, *key)
		return conn

	@synchronized
	def append_logs(self, task, logs):
		conn = self.__open_logs_conn(task)
		cur = conn.cursor()
		bi = BatchInsert(cur, "logs",
				["task_index", "timestamp", "level", "name", "msg"],
				batch_size = 1)
		for log in logs:
			timestamp = time.mktime(log[0].timetuple()) + 1e-6 * log[0].microsecond
			level = _LOG_LEVEL_ID.get(log[1], 0)
			bi.insert(task.index, timestamp, level, log[2], log[3])
		bi.close()
		conn.commit()
		cur.close()

	def clean(self):
		self.__conn_cache_clean(self)

	def close(self):
		# close cached connections
		# what about thread_id???
		pass