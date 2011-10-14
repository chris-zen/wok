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

from wok.server.common import wok, make_json_response

from flask import Module, abort

monitoring_api = Module(__name__)

@monitoring_api.route("/instance/state/<name>")
def instance_state(name):
	inst = wok().instance(name)
	if inst is None:
		abort(404)

	e = inst.to_element()

	return make_json_response(e.to_native())

@monitoring_api.route("/task/logs/<instance_name>/<module_id>/<task_index>")
def task_logs(instance_name, module_id, task_index):
	inst = wok().instance(instance_name)
	if inst is None:
		abort(404)

	module_id = ".".join([inst.root_node_name, module_id])
	
	#if not inst.task_exists(module_id, task_index):
	#	abort(404)

	try:
		task_index = int(task_index)
		
		logs = inst.task_logs(module_id, task_index)
		
		return make_json_response({
			"ok" : True,
			"logs" : logs })
	except Exception as e:
		if wok().conf.get("wok.server.debug", False, dtype=bool):
			raise
		
		return make_json_response({
			"ok" : False,
			"error" :  repr(e)})
