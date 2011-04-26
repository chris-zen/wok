import os
import json
import time

from wok.server.common import make_text_response

from flask import Module, request, session, redirect, url_for, \
	render_template, flash, current_app

web = Module(__name__)

def wok():
	return current_app.config["WOK"]

import re
log_re = re.compile("^.*(DEBUG|INFO|WARN|ERROR).*$")

def prepare_logs(output):
	logs = []
	for line in output.split("\n"):
		level = ""
		m = log_re.match(line)
		if m:
			level = m.group(1).lower()
		logs += [{"level" : level, "text" : line}]
	return logs

@web.route('/')
def index():
	return render_template('index.html')

@web.route('/conf')
def configuration():
	conf = wok().conf.to_native()
	conf_text = json.dumps(conf, indent=4)
	return render_template('conf.html', conf_text=conf_text)

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

	return render_template('workflow.html', workflow_text=wf)

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
		mnode = {}
		flash("Module configuration not available")

	return render_template('module.html', name=name, mnode=mnode)

@web.route('/module-conf/<name>')
def module_conf(name):
	title = "Module %s configuration" % name
	text = ""
	mnode_conf = wok().module_conf(name)
	if mnode_conf is None:
		flash("Module configuration not available")
	else:
		text = json.dumps(mnode_conf.to_native(), indent=4)

	return render_template('pygments.html', title=title, text=text, lang="javascript")

@web.route('/module-output/<name>')
def module_output(name):
	title = "Module %s output" % name
	output = wok().module_output(name)
	if output is None:
		logs = []
		flash("Module output not available")
	else:
		logs = prepare_logs(output)

	return render_template('logs.html', title=title, logs=logs)

@web.route('/task/<name>')
def task(name):
	task = wok().task_state(name)
	if task is None:
		task = {}
		flash("Task state not available")

	return render_template('task.html', name=name, task=task)

@web.route('/task-model/<name>')
def task_model(name):
	title = "Task %s model" % name
	text = ""
	try:
		task = wok().task_state(name) # TODO return None if doesn't exist
	except:
		task = None
	if task is None:
		flash("Task model not available")
	else:
		text = json.dumps(task.to_native(), indent=4)

	return render_template('pygments.html', title=title, text=text, lang="javascript")

@web.route('/task-conf/<name>')
def task_conf(name):
	title = "Task %s configuration" % name
	text = ""
	task_conf = wok().task_conf(name)
	if task_conf is None:
		flash("Task configuration not available")
	else:
		text = json.dumps(task_conf.to_native(), indent=4)

	return render_template('pygments.html', title=title, text=text, lang="javascript")

@web.route('/task-output/<name>')
def task_output(name):
	title = "Task %s output" % name
	output = wok().task_output(name)
	if output is None:
		logs = []
		flash("Task output not available")
	else:
		logs = prepare_logs(output)

	return render_template('logs.html', title=title, logs=logs)
