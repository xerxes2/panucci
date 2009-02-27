#!/usr/bin/env python
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

from distutils.core import setup
from glob import glob
import os

running_on_tablet = os.path.exists('/etc/osso_software_version')

applications_dir = 'share/applications'
if running_on_tablet:
    applications_dir += '/hildon'

data_files = [
    ('share/panucci', glob('icons/*.png')),
    (applications_dir, ['data/panucci.desktop']),
    ('share/icons/hicolor/scalable/apps', ['data/panucci.png']),
]
    
setup(name='Panucci',
      version='0.2',
      description='A Resuming Media Player',
      author='Thomas Perl',
      author_email='thp@perli.net',
      url='http://panucci.garage.maemo.org/',
      packages=['panucci'],
      package_dir={ '':'src' },
      scripts=['bin/panucci'],
      data_files=data_files,
     )
