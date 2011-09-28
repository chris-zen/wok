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

class Breadcrumb(object):
	def __init__(self, title, links=None):
		self.title = title
		if links is None:
			links = []
		self.links = links

class BcLink(object):
	def __init__(self, title, href):
		self.title = title
		self.href = href
