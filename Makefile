.PHONY: test release

all: test release

test:
	python setup.py test

release:
	python setup.py release sdist # upload