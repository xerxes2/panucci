PREFIX ?= /usr

all:
	@echo "Possible make targets:"
	@echo "    install - install the package"
	@echo "    clean - remove the build files"
	@echo "    distclean - remove build files + dist target"
	@echo "    test - test the application"

install: python-install post-install

python-install:
	python setup.py install --optimize 2

clean:
	rm -rf build src/panucci/*.pyc

distclean: clean
	rm -rf dist

test:
	PYTHONPATH=src/ python bin/panucci

post-install:
	gtk-update-icon-cache -f -i $(PREFIX)/share/icons/hicolor/
	update-desktop-database $(PREFIX)/share/applications/
