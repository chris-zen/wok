from time import strftime, gmtime

from flask import Flask
from werkzeug import ImmutableDict

from jinja2 import evalcontextfilter, Markup

from wok.server.views.web import web
from wok.server.views.restful import restful

class FlaskWithPygments(Flask):
	jinja_options = ImmutableDict(
		extensions = [
			'jinja2.ext.autoescape',
			'jinja2.ext.with_',
			'wok.server.jinja_pygments.PygmentsExtension']
	)

app = FlaskWithPygments(__name__)

app.secret_key = '|]\xb6v,\xe3{\xcd\xd4\xf1i\xd6\x80\xf7Z\x037\xab\xf1\xb4\xfaP\xf0\x8d'

app.register_module(web, url_prefix="")
app.register_module(restful, url_prefix="/restful")

@app.template_filter()
@evalcontextfilter
def elapsed_time(eval_ctx, value):
	result = strftime("%H:%M:%S", gmtime(value))
	if eval_ctx.autoescape:
		result = Markup(result)
	return result
