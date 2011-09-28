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

from flask import Module

monitoring_api = Module(__name__)

@monitoring_api.route("/instance/<name>")
def instance_state(name):
	inst = wok().instance(name)
	if inst is None:
		abort(404)

	e = inst.to_element()
	return make_json_response(e.to_native())
#	return make_json_response([
#			{
#				"name": "m1",
#				"state": "finished",
#				"state_msg": "Return code 0",
#				"tasks_count": { "failed": 0, "finished": 10, "running": 4, "queued": 9, "submitted": 6, "ready": 1 },
#				"children": [
#					{
#						"name": "m1.1",
#						"state": "finished",
#						"state_msg": "",
#						"tasks_count": { "failed": 6, "finished": 11, "running": 9, "queued": 0, "submitted": 3, "ready": 0 }
#					}
#				]
#			},
#			{
#				"name": "m2",
#				"state": "submitted",
#				"state_msg": "Queued",
#				"tasks_count": { "failed": 5, "finished": 5, "running": 10, "queued": 6, "submitted": 12, "ready": 10 }
#			},
#			{
#				"name": "m3",
#				"state": "ready",
#				"state_msg": "This is a long long long module state message",
#				"tasks_count": { "failed": 0, "finished": 0, "running": 10, "queued": 0, "submitted": 0, "ready": 10 }
#			}
#		])

