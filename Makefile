#
# This file is part of Panucci.
# Copyright (c) 2008-2009 The Panucci Audiobook and Podcast Player Project
#
# Panucci is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Panucci is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Panucci.  If not, see <http://www.gnu.org/licenses/>.
#

PREFIX ?= /usr
DESTDIR ?= /

PYTHON = /usr/bin/python2.5

all:
	@echo "Possible make targets:"
	@echo "    install - install the package"
	@echo "    clean - remove the build files"
	@echo "    distclean - remove build files + dist target"
	@echo "    test - test the application"

install: python-install post-install install-schemas
	replace @INSTALL_PREFIX@ $(DESTDIR)$(PREFIX) < \
	  data/panucci.service.in > data/panucci.service
	install data/panucci.service $(DESTDIR)$(PREFIX)/share/dbus-1/services/

python-install:
	$(PYTHON) setup.py install --optimize 2 --root=$(DESTDIR) --prefix=$(PREFIX)

copy-schemas:
	mkdir -p $(DESTDIR)/etc/gconf/schemas
	install data/panucci.schemas $(DESTDIR)/etc/gconf/schemas

install-schemas:
	GCONF_CONFIG_SOURCE=`gconftool-2 --get-default-source` \
		gconftool-2 --makefile-install-rule data/panucci.schemas
	# This isn't a problem, gconf gets started when it's needed
	# DON'T WORRY IF THIS FAILS, kay?
	-killall gconfd-2

post-install:
	gtk-update-icon-cache -f -i $(DESTDIR)$(PREFIX)/share/icons/hicolor/
	update-desktop-database $(DESTDIR)$(PREFIX)/share/applications/

clean:
	rm -rf build src/panucci/*.{pyc,pyo} data/panucci.service

distclean: clean
	rm -rf dist

test:
	PYTHONPATH=src/ python bin/panucci --debug

ptest:
	LD_LIBRARY_PATH=/usr/lib/gtk-2.0/modules GTK_MODULES=gtkparasite \
	PYTHONPATH=src/ python bin/panucci --debug

build-package:
	# See: http://wiki.maemo.org/Uploading_to_Extras#Debian_tooling
	dpkg-buildpackage -rfakeroot -sa -i -I.git

