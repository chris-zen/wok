from flask import Flask
from wok.server.views.web import web
from wok.server.views.restful import restful

app = Flask(__name__)

app.secret_key = '|]\xb6v,\xe3{\xcd\xd4\xf1i\xd6\x80\xf7Z\x037\xab\xf1\xb4\xfaP\xf0\x8d'

app.register_module(web, url_prefix="")
app.register_module(restful, url_prefix="/service")
