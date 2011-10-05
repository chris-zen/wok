.. _virtualenv: http://www.virtualenv.org/
.. _GitHub: https://github.com/chris-zen/wok

Installation
============

Dependencies
++++++++++++

Wok requeries Python 2.6 or above to be installed in the system.

It also depends on the following packages that are automatically installed if you follow the instructions in the following sections::

- lxml
- drmaa
- flask 0.6
- pygments

Installing from distribution
++++++++++++++++++++++++++++

Ideally you can just run the following command that will download and install Wok and the dependencies automatically::

	$ pip install -U https://github.com/chris-zen/wok/zipball/3.0.0

Alternatively you can download the package from the GitHub_ and uncompress it, then install Wok and its dependencies as::

	$ cd wok-3.x
	$ python setup.py install

To check that everything is ok ask for help::

	$ wok-run --help

Installing from source code
+++++++++++++++++++++++++++

If you want to work with the development branch of the version 2.x you need to checkout the source code from the git repository::

	$ git clone git://github.com/chris-zen/wok.git wok-3.x
	$ cd wok-3.x

Is is recommended to work with virtualenv_, it does provide a clever way to keep different project environments isolated. Just run the following command to create a virtual enviroment::

	$ virtualenv env
	$ . env/bin/activate

Now you are ready to install Wok and its dependencies. This will install the git head as the current version inside the virtual enviroment::
	
	$ python setup.py develop

Then you just have to run the following command to get the latest version::

	$ git pull origin

Generating documentation
------------------------

Once the source code has been checked out from the git repository, the included documentation can be compiled. You will need *sphinx* installed in your system. To install it use your system package repository manager (yum, apt-get, ...) or run the following command::

	$ pip install -U sphinx

Then run the following command to compile de documentation::

	$ cd wok-3.x
	$ make docs

The following files containing the documentation will be generated:

- *docs/wok-<version>.pdf*: A printable version of the documentation in PDF format.
- *docs/wok-docs.zip*: The full documentation in HTML format.

