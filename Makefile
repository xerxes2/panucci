all:
	@echo "Possible make targets:"
	@echo "    install - install the package"
	@echo "    clean - remove the build files"
	@echo "    distclean - remove build files + dist target"
	@echo "    test - test the application"

install:
	python setup.py install --optimize 2

clean:
	rm -rf build src/panucci/*.pyc

distclean: clean
	rm -rf dist

test:
	PYTHONPATH=src/ python bin/panucci

