.PHONY: clean-pyc test upload-docs docs

all: clean-pyc docs

test:
	python setup.py test

release:
	python setup.py release sdist # upload

clean-pyc:
	find . -name '*.pyc' -exec rm -f {} +
	find . -name '*.pyo' -exec rm -f {} +
	find . -name '*~' -exec rm -f {} +

upload-docs:

docs:
	$(MAKE) -C doc clean html dirhtml latex
	$(MAKE) -C doc/build/latex all-pdf
	cd doc/build/; mv html wok-docs; rm wok-docs.zip; zip -r wok-docs.zip wok-docs; mv wok-docs html
	cp doc/build/latex/wok.pdf doc/
