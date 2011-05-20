"""

"""

import distribute_setup
distribute_setup.use_setuptools()

from setuptools import setup, find_packages
setup(
    name = "wok",
    version = "2.0.2",
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
		'Flask>=0.6'
	],

    package_data = {
        # If any package contains *.txt or *.rst files, include them:
        '' : ['*.txt', '*.pdf', '*.html']
    },

    # metadata for upload to PyPI
    author = "Christian Perez-Llamas",
    author_email = "christian.perez@upf.edu",
    description = "Workflow management system",
    license = "NOSL 3.0",
    keywords = "workflow dataflow analysis",
    url = "http://bg.upf.edu/forge",
	long_description = __doc__

    # could also include long_description, download_url, classifiers, etc.
)
