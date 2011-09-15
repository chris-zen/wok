# ******************************************************************
# Copyright 2009-2011, Universitat Pompeu Fabra
#
# Licensed under the Non-Profit Open Software License version 3.0
# ******************************************************************

import os
import json
import time

from wok.server.common import Breadcrumb, BcLink

from flask import Module, request, session, redirect, url_for, \
	render_template, flash, current_app

web = Module(__name__)

def wok():
	return current_app.config["WOK"]

@web.route('/')
def index():
	return render_template('index.html')

@web.route('/templates')
def templates():
	return render_template('index.html')

@web.route('/instances')
def instances():
	return render_template('index.html')

@web.route('/files')
def files():
	return render_template('index.html')

@web.route('/settings')
def settings():
	return render_template('index.html')