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

from wok.server.common import wok, make_json_response, make_text_response

from flask import Module, abort, request

monitoring_api = Module(__name__)

__STR_TO_BOOL = {
	"0" : False, "1" : True,
	"false" : False, "true" : True }

def bool_arg(key, default = None):
	if key not in request.args:
		return default

	v = request.args[key].lower()
	if v in __STR_TO_BOOL:
		return __STR_TO_BOOL[v]

	return False

# Instance ---------------------------------------------------------------------

@monitoring_api.route("/instance/state/<instance_name>")
def instance_state(instance_name):
	inst = wok().instance(instance_name)
	if inst is None:
		abort(404)

	e = inst.to_element()

	return make_json_response(e.to_native())

@monitoring_api.route("/instance/control/<instance_name>")
def instance_control(instance_name):
	inst = wok().instance(instance_name)
	if inst is None:
		abort(404)

	action = request.args.get("action")
	if action is None:
		return make_json_response({
			"ok" : False,
			"instance" : instance_name,
			"error" : "'action' argument not specified" })

	if action not in ["start", "pause", "stop", "reset", "reload"]:
		return make_json_response({
			"ok" : False,
			"instance" : instance_name,
			"error" : "Unknown 'action': %s" % action })

	prev_state = str(inst.state)

	try:
		if action == "start":
			inst.start()
		elif action == "pause":
			inst.pause()
		elif action == "stop":
			inst.stop()
		elif action == "reset":
			inst.reset()
		elif action == "reload":
			inst.reload()

		new_state = str(inst.state)

	except Exception as ex:
		return make_json_response({
			"ok" : False,
			"instance" : instance_name,
			"error" : str(ex) })

	return make_json_response({
		"ok" : True,
		"instance" : instance_name,
		"previous_state" : prev_state,
		"current_state" : new_state })

@monitoring_api.route("/instance/repr/<instance_name>")
def instance_repr(instance_name):
	inst = wok().instance(instance_name)
	if inst is None:
		abort(404)
	return make_text_response(repr(inst))

# Module -----------------------------------------------------------------------

@monitoring_api.route("/module/conf/<instance_name>/<module_id>")
def module_conf(instance_name, module_id):
	inst = wok().instance(instance_name)
	if inst is None:
		abort(404)
	
	#if not inst.module_exists(module_id):
	#	abort(404)

	expanded = bool_arg("expanded", False)
	
	conf = inst.module_conf(module_id, expanded = expanded)

	return make_json_response(conf.to_native())

# Task -------------------------------------------------------------------------

@monitoring_api.route("/task/logs/<instance_name>/<module_id>/<task_index>")
def task_logs(instance_name, module_id, task_index):
	inst = wok().instance(instance_name)
	if inst is None:
		abort(404)

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
