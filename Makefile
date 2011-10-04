.PHONY: test release clean-pyc docs upload-docs

all: test clean-pyc docs release

test:
	python setup.py test

clean-pyc:
	find . -name '*.pyc' -exec rm -f {} +
	find . -name '*.pyo' -exec rm -f {} +
	find . -name '*~' -exec rm -f {} +

docs:
	$(MAKE) -C doc clean html dirhtml latex
	$(MAKE) -C doc/build/latex all-pdf
	cd doc/build/; mv html wok-docs; rm wok-docs.zip; zip -r wok-docs.zip wok-docs; mv wok-docs html
	cp doc/build/latex/wok*.pdf doc/

upload-docs: docs


release:
	python setup.py release sdist # upload
