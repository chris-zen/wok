import json

from flask import Module, \
	make_response, current_app

restful = Module(__name__)

def wok():
	return current_app.config["WOK"]

def json_plain(obj):
	st = json.dumps(obj, indent=4)
	response = make_response(st)
	response.headers["Content-Type"] = "text/plain" # weblication/json
	return response

@restful.route("/")
def test():
	return "RESTFUL OK"