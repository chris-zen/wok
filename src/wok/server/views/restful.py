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

from wok.server.common import make_xml_response, make_json_response, make_text_response

from flask import Module, current_app

restful = Module(__name__)

def wok():
	return current_app.config["WOK"]

@restful.route("/")
def test():
	return "RESTFUL OK"

@restful.route('/conf')
def conf():
	return make_json_response(wok().conf.to_native())

@restful.route('/workflow')
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

@restful.route('/module-conf/<name>')
def module_conf(name):
	module_conf = wok().module_conf(name)
	if module_conf is None:
		abort(404)

	return make_json_response(module_conf.to_native())

@restful.route('/module-output/<name>')
def module_output(name):
	output = wok().module_output(name)
	if output is None:
		abort(404)

	return make_text_response(output)

@restful.route('/task/<name>')
def task(name):
	task = wok().task_state(name)
	if task is None:
		abort(404)

	return make_json_response(task.to_native())

@restful.route('/task-conf/<name>')
def task_conf(name):
	task_conf = wok().task_conf(name)
	if task_conf is None:
		abort(404)

	return make_json_response(task_conf.to_native())

@restful.route('/task-output/<name>')
def task_output(name):
	output = wok().task_output(name)
	if output is None:
		abort(404)

	return make_text_response(output)
