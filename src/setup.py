"""
Wok is a workflow management system implemented in Python that makes very easy
to structure the workflows, parallelize their execution
and monitor its progress easily.

It is designed in a modular way allowing to adapt it to different infraestructures.

For the time being it is strongly focused on clusters implementing
any DRMAA compatible resource manager such as Sun Grid Engine
among others with a shared folder among work nodes.

Other, more flexible infrastructures (such as the cloud)
are being studied for future implementations.
"""

import distribute_setup
distribute_setup.use_setuptools()

from setuptools import setup, find_packages
setup(
    name = "wok",
    version = "3.0.0",
    packages = find_packages(),
    scripts = [
		'wok-run.py'
	],

    # Project uses reStructuredText, so ensure that the docutils get
    # installed or upgraded on the target machine
    install_requires = [
		'docutils>=0.3',
		'lxml>=2.3',
		'drmaa',
		'Flask=0.6'
	],

    package_data = {
        # If any package contains *.txt or *.pdf files, include them:
        '' : ['*.txt', '*.pdf', '*.html']
    },

    # metadata for upload to PyPI
    author = "Christian Perez-Llamas",
    author_email = "christian.perez@upf.edu",
    description = "Workflow management system",
    license = "NOSL 3.0",
    keywords = "workflow dataflow analysis parallel",
    url = "http://bg.upf.edu/wok",
	long_description = __doc__

    # could also include long_description, download_url, classifiers, etc.
)
