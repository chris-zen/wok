.. _JSON: http://en.wikipedia.org/wiki/JSON
.. _DRMAA: http://en.wikipedia.org/wiki/DRMAA

Configuration
=============

Wok implements a flexible system for configuration using JSON_ files and command line directives.

Basically a json file allows to repressent structured data using dictionaries, lists and simple types such as text, numbers and boolean (true or false). The configuration file must have a dictionary as the root element, and each key in it represent a section or a parameter.

On the other hand comand line directives allows to specify parameter values using paths, for example the following directive::

	wok.log.level=debug

will result in the following JSON representation::

	{
		"wok" : {
			"log" : {
				"level" : "debug"
			}
		}
	}

The configuration can be splited in many different files and can include not only the configuration required by *Wok* but also the one required by the workflow. All the configuration files and directives are merged in one document. It allows expansion of variables, so one configuration file can reference variables defined in other files. The order in which the files and directives are specified matters. If two configuration files define the same variable, the latter will override the previous one. The overriding is mainly used to change the configuration of an instance without having to modify any file.

There are also internal configuration parameters that are introduced by *Wok*, all of them start with "__" and in some situations it could be useful to use them, for example *wok.__instance.name*.

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
			"work_path" : "/tmp/work/43ffa633-e4c0-47ff-a83b-611f1d441fdc",

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
		}
	}

Configuration parameters
++++++++++++++++++++++++

**wok**
	This section contains all the configuration related with the *Wok* system.

	**work_path**
		The path where the engine state files will be saved. If the path doesn't exist it will be created automatically.
		One trick to avoid collisions between different instances of *Wok* is to use a path containing ${**wok.__instance.name**}

	**defaults**
		This section contains default values for common parameters.

		**maxpar**
			In case a module doesn't specify the *maxpar* parameter this will be the value used. By default it is 0 which means that there is no limit.

		**wsize**
			In case a module doesn't specify the *wsize* parameter this will be the value used. By default it is 1.

	**install_path** [*Internal*]
		This is the path where *Wok* is installed.

	**log**
		This section contains the configuration specific to the *Wok* engine logger.

		**level**
			This param allows to configure how much verbose the output is. There are four levels from more to less log messages:

			- **debug**: Shows debug messages plus the following level messages.
			- **info**: Shows information messages plus the following level messages.
			- **warn**: Shows warning messages plus the following level messages.
			- **error**: Shows only error messages.

	**server**
		This section contains the configuration for the web server.

		**enabled**
			A boolean (*true* or *false*) specifying if the web server should be enabled.

		**host**
			It is the network interface where the server listens for requests. By default it is *127.0.0.1* which means that only can be accessed from the local machine where wok-run.py is launched. To have access from other machines it should have the value *0.0.0.0*.

		**port**
			Determines the TCP port. By default it is 5000, but when many workflows has to be run simultaneusly each one has to listen in a different port.

		**debug**
			A boolean (*true* or *false*) specifying if the web server should be started in debug mode. It is useful for *Wok* developers only.

		**engine_start**
			When the web server is enabled, by default, *Wok* is started with the workflow stoped and prepared to be executed, waiting for the user to activate it.
			You can force *Wok* to start the execution of the workflow just after the web server is started using this parameter.
			It can be *true* to immediately start the execution or *false* to wait for the user activation.

		**log**
			This section contains the configuration specific to the web server logger. See **wok.log** for more details.

	**job_manager**
		The job manager to use to manage task execution. There are two available:

		- **mcore**: To use in multi-core machines. It allows to run tasks in parallel using all the processors of a machine.
		- **drmaa**: To interface with a DRMAA_ compatible resource manager such as Sun Grid Engine, SLURM, Torque and many more. It is more convenient for running tasks in a cluster.

	**job_managers**
		This section contains default configuration for each type of job manager.
		Each job manager will have its own subsection.

		**default**
			This section contains configuration applicable to all the schedullers.

			**work_path**
				This variable is automatically managed by the *Wok* engine, but can be overriden. The working path to store state files related with the scheduler.

			**output_path**
				This variable is automatically managed by the *Wok* engine, but can be overriden.The path to store tasks standard output and error.

			**working_directory**
				The default working directory for tasks.

			**log**
				This section contains the configuration specific to the job manager logger. See **wok.log** for more details.

		**mcore**
			This section contains configuration specific to the multi-core job manager. It allows all the configuration parameters explained in **default** plus:

			**max_cores**
				The maximum number of cores to use. By default, it will use all the available cores.

		**drmaa**
			This section contains configuration for the DRMAA job manager. It allows all the configuration parameters explained in **default**.

	**execution**
		This section contains configuration specific to execution of tasks:

		**mode**
			A module can be executed in different ways depending on the workflow specification.
			In this section the default configuration for the different execution modes available can be specified.

			**native**
				This execution mode is used for wok native task implementations.

				**env**
					This section allows to define enviroment variables, for example::

						{ "wok" : { "launchers" : { "native" : {
							"env" : {
								"EDITOR" : "vim",
								"TERM" : "xterm"
							}
						} } } }

				**python**
					When the python implementation of the wok framework is used these parameters can be configured:

					**bin**
						The path to the python binary to use. By default is *python* so it will take into account the defined *PATH*. This is not recommended as in a cluster enviroment could not coincide in the worker nodes with the launcher node.

					**lib_path**
						The paths that will be suffixed to the system defined enviroment variable PYTHONPATH. Example::

							{ "wok" : { "launchers" : { "native" : { "python" : {
								"lib_path" : [
									"${wok.install_path}",
									"/opt/mylib"
								]
							} } } } }

			**shell**
				This execution mode is used when a command line is directly specified in the module.

				**bin**
					The default shell binary path to use. By default the one defined in the system is used.

				**env**
					This section allows to define enviroment variables, for example::

						{ "wok" : { "launchers" : { "shell" : {
							"env" : {
								"EDITOR" : "vim",
								"TERM" : "xterm"
							}
						} } } }

	**storage**
		*TODO*

Internal parameters
+++++++++++++++++++

**wok**

	**__instance**
		This section contains instance specific parameters.

		**name**
			The current instance name. It is generated automatically at the begining with a UUID. It can be overriden by the user. This allows to have many instances of the same workflow without collisions if it is used to configure working paths. Example:

			**my.conf**
			::

				{
					"base_path" : "/tmp",
					"wok" : {
						"work_path" : "${base_path}/work/${wok.__instance.name}"
					}
				}

				$ wok-run.py -c my.conf -D x=3 -D wok.__instance.name=test1 my.flow

				$ wok-run.py -c my.conf -D x=7 -D wok.__instance.name=test2 my.flow

	**__flow**
		This section contains workflow specific parameters.

		**path**
			The base path of the workflow definition file. 

		**file**
			The file name of the workflow definition file.

	**__cwd**
		The path from which *Wok* has been started.
