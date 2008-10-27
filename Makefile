PREFIX ?= /usr
DESTDIR ?= /

all:
	@echo "Possible make targets:"
	@echo "    install - install the package"
	@echo "    clean - remove the build files"
	@echo "    distclean - remove build files + dist target"
	@echo "    test - test the application"

install: python-install post-install install-schemas

python-install:
	python setup.py install --optimize 2

install-schemas:
	install data/panucci.schemas $(DESTDIR)/etc/gconf/schemas
	GCONF_CONFIG_SOURCE=`gconftool-2 --get-default-source` \
		gconftool-2 --makefile-install-rule data/panucci.schemas
	# This isn't a problem, gconf gets started when it's needed
	# DON'T WORRY IF THIS FAILS, kay?
	-killall gconfd-2

clean:
	rm -rf build src/panucci/*.pyc

distclean: clean
	rm -rf dist

test:
	PYTHONPATH=src/ python bin/panucci

post-install:
	gtk-update-icon-cache -f -i $(PREFIX)/share/icons/hicolor/
	update-desktop-database $(PREFIX)/share/applications/
