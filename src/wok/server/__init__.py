# ******************************************************************
# Copyright 2009, Universitat Pompeu Fabra
#
# Licensed under the Non-Profit Open Software License version 3.0
# ******************************************************************

from time import strftime, gmtime

from flask import Flask
from werkzeug import ImmutableDict

from jinja2 import evalcontextfilter, Markup

from wok.server.views.api import api
from wok.server.views.home import home
from wok.server.views.workflows import workflows
from wok.server.views.monitoring import monitoring
from wok.server.views.files import files
from wok.server.views.settings import settings

class FlaskWithPygments(Flask):

	jinja_options = ImmutableDict(
		extensions = [
			'jinja2.ext.autoescape',
			'jinja2.ext.with_',
			'wok.server.jinja_pygments.PygmentsExtension']
	)

app = FlaskWithPygments(__name__)

app.secret_key = '|]\xb6v,\xe3{\xcd\xd4\xf1i\xd6\x80\xf7Z\x037\xab\xf1\xb4\xfaP\xf0\x8d'

app.register_module(api, url_prefix="/api")

app.register_module(home, url_prefix="")
app.register_module(workflows, url_prefix="/workflows")
app.register_module(monitoring, url_prefix="/monitoring")
app.register_module(files, url_prefix="/files")
app.register_module(settings, url_prefix="/settings")

@app.template_filter()
@evalcontextfilter
def elapsed_time(eval_ctx, value):
	result = strftime("%H:%M:%S", gmtime(value))
	if eval_ctx.autoescape:
		result = Markup(result)
	return result
