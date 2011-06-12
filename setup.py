#!/usr/bin/env python
#
# This file is part of Panucci.
# Copyright (c) 2008-2011 The Panucci Project
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

from distutils.core import setup

import glob
import os
import sys

SRC_DIR = 'src/'

d2p = lambda d: d[len(SRC_DIR):].replace('/', '.')
PACKAGES = [d2p(d) for d, dd, ff in os.walk(SRC_DIR) if '__init__.py' in ff]

SCRIPTS = glob.glob('bin/*')

if not os.path.exists('data/panucci.service') and 'clean' not in sys.argv:
    print >>sys.stderr, """
    data/panucci.service not found. Maybe you want to run
    "make install" instead of using setup.py directly?
    """
    sys.exit(1)

DATA_FILES = [
    ('share/panucci', glob.glob('icons/*.png')),
    ('share/panucci', glob.glob('data/ui/qml/*.qml')),
    ('share/panucci', ['data/panucci.conf', 'data/panucci-all.conf']),
    ('share/applications', ['data/panucci.desktop']),
    ('share/icons/hicolor/scalable/apps', ['data/panucci.svg']),
    ('share/icons/hicolor/64x64/apps', ['data/panucci.png']),
    ('share/dbus-1/services', ['data/panucci.service']),
]

mo_files = glob.glob('data/locale/*/LC_MESSAGES/panucci.mo')

if len(mo_files) == 0:
    print >>sys.stderr, """
    Warning: No translation files found. Maybe you want to
    run "make install" instead of using setup.py directly?
    """

for mofile in mo_files:
    modir = os.path.dirname(mofile).replace('data', 'share')
    DATA_FILES.append((modir, [mofile]))

sys.path.insert(0, SRC_DIR)
import panucci

setup(
        name='Panucci',
        version=panucci.__version__,
        description='Resuming audiobook and podcast player',
        author='Thomas Perl',
        author_email='thp@gpodder.org',
        url='http://gpodder.org/panucci/',
        packages=PACKAGES,
        package_dir={ '': SRC_DIR },
        scripts=SCRIPTS,
        data_files=DATA_FILES,
)
