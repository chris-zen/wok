import os.path
import sqlite3

class SqliteEngineDB(object):
	def __init__(self, engine):
		self._engine = engine

		self._base_path = os.path.join(engine.work_path, "db")

		self._global_db_file = os.path.join(self._base_path, "__engine.db")
		self._global_conn = None

		self._instances_conn = {}

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
		#c.execute("CREATE TABLE logs ()")
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
		conn = self.__open_instance_conn(instance)
		#TODO ...
		self.__close_instance_conn(conn, instance)

