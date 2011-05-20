wok-run.py
==========

This is the script that executes a workflow.

::
	Usage: wok-run.py [options] <flow-file>

	Options:
	  --version             show program's version number and exit
	  -h, --help            show this help message and exit
	  -L LOG_LEVEL, --log-level=LOG_LEVEL
	                        Which log level: debug, info, warn, error, critical,
	                        notset
	  -c FILE, --conf=FILE  Load configuration from a file. Multiple files can be
	                        specified
	  -D PARAM=VALUE        External data value. example -D param1=value

Example::

	$ wok-run.py -c laptop.conf -c common.conf -D wok.server=true mrna/mrna.flow
