
# 
# Copyright (c) 2008 The Panucci Audiobook and Podcast Player Project
# 
# Permission is hereby granted, free of charge, to any person obtaining
# a copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject to
# the following conditions:
# 
# The above copyright notice and this permission notice shall be included
# in all copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
# IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY
# CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
# TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
# SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
# 

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
	PYTHONPATH=src/ python bin/panucci --debug

post-install:
	gtk-update-icon-cache -f -i $(PREFIX)/share/icons/hicolor/
	update-desktop-database $(PREFIX)/share/applications/
