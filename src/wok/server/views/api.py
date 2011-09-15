# ******************************************************************
# Copyright 2009-2011, Universitat Pompeu Fabra
#
# Licensed under the Non-Profit Open Software License version 3.0
# ******************************************************************

from wok.server.common import make_xml_response, make_json_response, make_text_response

from flask import Module, current_app

api = Module(__name__)

def wok():
	return current_app.config["WOK"]

@api.route("/")
def test():
	return "RESTFUL OK"

@api.route('/conf')
def conf():
	return make_json_response(wok().conf.to_native())

@api.route('/workflow')
def workflow():
	conf = wok().conf
	path = os.path.join(conf["wok.__flow.path"], conf["wok.__flow.file"])
	f = open(path)
	try:
		wf = f.read()
	finally:
		f.close()

	if wf is None:
		abort(404)

	return make_xml_response(wf)

@api.route('/module-conf/<name>')
def module_conf(name):
	module_conf = wok().module_conf(name)
	if module_conf is None:
		abort(404)

	return make_json_response(module_conf.to_native())

@api.route('/module-output/<name>')
def module_output(name):
	output = wok().module_output(name)
	if output is None:
		abort(404)

	return make_text_response(output)

@api.route('/task/<name>')
def task(name):
	task = wok().task_state(name)
	if task is None:
		abort(404)

	return make_json_response(task.to_native())

@api.route('/task-conf/<name>')
def task_conf(name):
	task_conf = wok().task_conf(name)
	if task_conf is None:
		abort(404)

	return make_json_response(task_conf.to_native())

@api.route('/task-output/<name>')
def task_output(name):
	output = wok().task_output(name)
	if output is None:
		abort(404)

	return make_text_response(output)
