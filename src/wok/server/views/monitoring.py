# ******************************************************************
# Copyright 2009, Universitat Pompeu Fabra
#
# Licensed under the Non-Profit Open Software License version 3.0
# ******************************************************************

from wok.server.common import wok, Breadcrumb, BcLink

from flask import Module, request, session, redirect, url_for, \
	render_template, flash, current_app

monitoring = Module(__name__)

@monitoring.route('/')
def index():
	return render_template('monitoring.html')

@monitoring.route('/instance/<name>')
def instance(name):
	return render_template('monitoring/instance.html', name = name)