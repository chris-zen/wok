Configuration
=============

Wok implements a flexible system for configuration based on JSON files and command line directives.

The configuration can be splited in many different files and can include not only the configuration required by *Wok* but also the one required by the workflow. All the configuration files and directives are merged in one document. It allows expansion of variables, so one configuration file can reference variables defined in other files. The order in which the files and directives are specified matters. If two configuration files define the same variable, the latter will override the previous one. The overriding is mainly used to change some configuration by using directives. There are also internal configuration variables that are introduced by *Wok*, all of them start with "__" and in some situations it could be useful to use them, for example *wok.__instance.name*.

Let's see some examples:

Given this configuration files:

**paths.conf**
::

	{
		"soft_path" : "/opt",
		"base_path" : "/tmp"
	}

**wok.conf**
::

	{
		"wok" : {
			"install_path" : "${soft_path}/wok/src",
			"work_path" : "${base_path}/work/${wok.__instance.name}"

			"log" : {
				"level" : "warn"
			}
		}
	}

When executing the following command::

	$ wok-run.py -c paths.conf -c wok.conf -D wok.log.level=info

the resulting configuration is::

	{
		"soft_path" : "/opt",
		"base_path" : "/tmp",

		"wok" : {
			"install_path" : "/opt/wok/src",
			"work_path" : "/tmp/work/43ffa633-e4c0-47ff-a83b-611f1d441fdc"

			"log" : {
				"level" : "info"
			}
		}
	}

and when executing::

	$ wok-run.py -c paths.conf -D soft_path=/usr/local -c wok.conf -D wok.__instance.name=run1

the resulting configuration is::

	{
		"soft_path" : "/usr/local",
		"base_path" : "/tmp",

		"wok" : {
			"install_path" : "/usr/local/wok/src",
			"work_path" : "/tmp/work/run1"

			"log" : {
				"level" : "warn"
			}
		}
	}

Wok configuration
+++++++++++++++++

All the configuration related with Wok system goes inside the wok section.

wok.install_path
wok.bin_path
wok.work_path
wok.auto_remove.task
wok.auto_remove.output
wok.clean
wok.scheduler
wok.schedulers
wok.schedulers.__default
wok.schedulers.__default.log
wok.schedulers.__default.log.level
wok.launchers
wok.log
wok.log.level
wok.defaults
wok.defaults.maxpar
wok.defaults.wsize
