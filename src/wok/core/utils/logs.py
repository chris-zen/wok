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

import re
from datetime import datetime

# 2011-10-06 18:39:46,849 bfast_localalign-0000 INFO  : hello world
_LOG_RE = re.compile("^(\d\d\d\d-\d\d-\d\d) (\d\d:\d\d:\d\d),\d\d\d (.*) (DEBUG|INFO|WARN|ERROR) +: (.*)$")

def parse_log(line):
	m = _LOG_RE.match(line)
	if m:
		timestamp = datetime.strptime(
						m.group(1) + " " + m.group(2),
						"%Y-%m-%d %H:%M:%S")
		name = m.group(3)
		level = m.group(4).lower()
		text = m.group(5).decode("utf-8", "replace")
	else:
		timestamp = None
		name = None
		level = None
		text = line.decode("utf-8", "replace")

	return (timestamp, level, name, text)