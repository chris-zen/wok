.PHONY: clean-pyc test upload-docs docs

all: clean-pyc docs

test:
	$(MAKE) -C src test

release:
	$(MAKE) -C src release

clean-pyc:
	find . -name '*.pyc' -exec rm -f {} +
	find . -name '*.pyo' -exec rm -f {} +
	find . -name '*~' -exec rm -f {} +

upload-docs:
	#scp -r docs/build/dirhtml/* pocoo.org:/var/www/flask.pocoo.org/docs/
	#scp -r docs/build/latex/wok.pdf pocoo.org:/var/www/flask.pocoo.org/docs/flask-docs.pdf
	#scp -r docs/build/wok-docs.zip pocoo.org:/var/www/flask.pocoo.org/docs/

docs:
	$(MAKE) -C doc html dirhtml latex
	$(MAKE) -C doc/build/latex all-pdf
	cd doc/build/; mv html wok-docs; zip -r wok-docs.zip wok-docs; mv wok-docs html
	cp doc/build/latex/wok.pdf doc/
