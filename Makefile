all:
	@echo "Possible make targets:"
	@echo "    install - install the package"
	@echo "    clean - remove the build files"
	@echo "    test - test the application"

install:
	python setup.py install

clean:
	rm -fr build src/panucci/*.pyc

test:
	PYTHONPATH=src/ python bin/panucci
