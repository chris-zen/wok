# ******************************************************************
# Copyright 2009-2011, Universitat Pompeu Fabra
#
# Licensed under the Non-Profit Open Software License version 3.0
# ******************************************************************

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

