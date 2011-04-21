import os
import json
import time

from flask import Module, request, session, redirect, url_for, \
	abort, render_template, flash, make_response, current_app

web = Module(__name__)

def wok():
	return current_app.config["WOK"]

def json_plain(obj):
	st = json.dumps(obj, indent=4)
	response = make_response(st)
	response.headers["Content-Type"] = "text/plain" # weblication/json
	return response

@web.route("/test")
def test():
	return json_plain({"a":1,"b":[1,2,3]})

@web.route('/')
def index():
	return render_template('index.html')

@web.route('/conf')
def configuration():
	return json_plain(wok().conf.to_native())
	#return jsonify(conf.to_native())
	#return render_template('conf.html', conf=conf)

@web.route('/workflow')
def workflow():
	conf = wok().conf
	path = os.path.join(conf["wok.__flow.path"], conf["wok.__flow.file"])
	f = open(path)
	try:
		wf = f.read()
	finally:
		f.close()

	if wf is None:
		flash("'%s' not found" % path)
		return render_template('workflow.html')

	response = make_response(wf)
	response.headers["Content-Type"] = "text/plain" # weblication/xml
	return response
	#return render_template('workflow.html', wf=wf)

@web.route('/state')
def state():
	return render_template('state.html', state=wok().state())

@web.route('/login', methods=['GET', 'POST'])
def login():
	error = None
	if request.method == 'POST':
		if request.form['password'] != '1234':
			error = 'Invalid password'
		else:
			session['logged_in'] = True
			flash('You were logged in')
			return redirect(url_for('index'))
	return render_template('login.html', error=error)

@web.route('/logout')
def logout():
	session.pop('logged_in', None)
	flash('You were logged out')
	return redirect(url_for('index'))

@web.route('/engine/start')
def engine_start():
	wok().start()
	time.sleep(0.5)
	return redirect(url_for('state'))

@web.route('/engine/pause')
def engine_pause():
	wok().pause()
	time.sleep(0.5)
	return redirect(url_for('state'))

@web.route('/engine/continue')
def engine_continue():
	wok().cont()
	time.sleep(0.5)
	return redirect(url_for('state'))

@web.route('/engine/stop')
def engine_stop():
	wok().stop()
	time.sleep(0.5)
	return redirect(url_for('state'))

def kill_process(pid):
	import os
	import signal
	import time
	time.sleep(0.2)
	os.kill(pid, signal.SIGINT)

@web.route('/engine/exit')
def engine_exit():
	wok().exit()
	import os
	pid = os.getpid()
	from multiprocessing import Process
	Process(target = kill_process, args=(pid,)).start()
	return render_template('exit.html')

@web.route('/module/<name>')
def module(name):
	mnode = wok().mnode_state(name)
	if mnode is None:
		abort(404)
	return render_template('module.html', name=name, mnode=mnode)

@web.route('/module-conf/<name>')
def module_conf(name):
	if request.args.get("dwl", 0, type=int) != 1:
		flash("JSON viewer not implemented yet")
		return redirect(url_for('state'))

	mnode_conf = wok().mnode_conf(name)
	if mnode_conf is None:
		abort(404)

	return json_plain(mnode_conf.to_native())

@web.route('/module-output/<name>')
def module_output(name):
	"""
	output = wok().task_output(name)
	if output is None:
		flash("Task '%s' output is not available" % name)
		return redirect(url_for('task', name=name))
	"""
	output = "Not implemented yet"
	response = make_response(output)
	response.headers["Content-Type"] = "text/plain"
	return response

@web.route('/task/<name>')
def task(name):
	task = wok().task_state(name)
	if task is None:
		abort(404)

	if request.args.get("dwl", 0, type=int) == 0:
		return render_template('task.html', name=name, task=task)
	else:
		#return jsonify(task.to_native())
		return json_plain(task.to_native())

@web.route('/task-conf/<name>')
def task_conf(name):
	if request.args.get("dwl", 0, type=int) != 1:
		flash("JSON viewer not implemented yet")
		return redirect(url_for('task', name=name))

	task_conf = wok().task_conf(name)
	if task_conf is None:
		abort(404)

	#return jsonify(task_conf.to_native())
	return json_plain(task_conf.to_native())

@web.route('/task-output/<name>')
def task_output(name):
	output = wok().task_output(name)
	if output is None:
		flash("Task '%s' output is not available" % name)
		return redirect(url_for('task', name=name))

	response = make_response(output)
	response.headers["Content-Type"] = "text/plain"
	return response
