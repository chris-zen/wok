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

import os.path
import sys
sys.path.insert(0, os.path.join(os.path.dirname(sys.argv[0]), "src"))

from wok import VERSION, AUTHORS, AUTHORS_EMAIL

setup(
    name = 'wok',
    version = VERSION,
    packages = find_packages('src'),
    package_dir = { '': 'src' },
    scripts = [
		'src/wok-run'
	],

    # Project uses reStructuredText, so ensure that the docutils get
    # installed or upgraded on the target machine
    install_requires = [
		'docutils>=0.3',
		'lxml>=2.3',
		'drmaa',
		'Flask==0.6',
		'pygments'
	],

    package_data = {
        # If any package contains *.txt or *.pdf files, include them:
        '' : ['*.txt', '*.pdf', '*.html']
    },

    # metadata for upload to PyPI
    author = AUTHORS,
    author_email = AUTHORS_EMAIL,
    description = 'Workflow management system',
    license = 'GPL 3.0',
    keywords = 'workflow dataflow analysis parallel',
    url = "https://github.com/chris-zen/wok",
	long_description = __doc__,

	classifiers = [
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU General Public License (GPL)',
		'Environment :: Console',
		'Environment :: Web Environment',
		'Intended Audience :: Science/Research',
		'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Topic :: Scientific/Engineering',
		'Topic :: Scientific/Engineering :: Bio-Informatics'
    ]

    # could also include download_url, etc.
)
