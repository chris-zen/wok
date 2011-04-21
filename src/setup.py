from setuptools import setup, find_packages
setup(
    name = "wok",
    version = "2.0.1",
    packages = find_packages(),
    scripts = [
		'wok-run.py'
	],

    # Project uses reStructuredText, so ensure that the docutils get
    # installed or upgraded on the target machine
    install_requires = [
		'docutils>=0.3'
	],

    package_data = {
        # If any package contains *.txt or *.rst files, include them:
        '' : ['*.txt', '*.rst']
    },

    # metadata for upload to PyPI
    author = "Christian Perez-Llamas",
    author_email = "christian.perez@upf.edu",
    description = "Workflow management system",
    license = "NOSL",
    keywords = "workflow dataflow analysis",
    url = "http://bg.upf.edu/forge"

    # could also include long_description, download_url, classifiers, etc.
)