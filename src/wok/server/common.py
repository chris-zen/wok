import json

from flask import make_response

def make_xml_response(obj):
	response = make_response(obj)
	response.headers["Content-Type"] = "application/xml"
	return response

def make_json_response(obj):
	st = json.dumps(obj, indent=4)
	response = make_response(st)
	response.headers["Content-Type"] = "application/json"
	return response

def make_text_response(obj):
	response = make_response(str(obj))
	response.headers["Content-Type"] = "text/plain"
	return response
