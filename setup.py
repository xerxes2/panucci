#!/usr/bin/env python

from distutils.core import setup
from glob import glob
import os

running_on_tablet = os.path.exists('/etc/osso_software_version')

data_files = [('share/panucci', glob('icons/*.png')), ]

if running_on_tablet :
    data_files += [
        ('share/applications/hildon', ['data/maemo/panucci.desktop']),
    ]
else:
    data_files += [
        ('share/applications', ['data/panucci.desktop']),
    ]
    
setup(name='Panucci',
      version='0.2',
      description='A Resuming Media Player',
      author='Thomas Perl',
      author_email='thp@perli.net',
      url='http://thpinfo.com/2008/panucci/',
      packages=['panucci'],
      package_dir={ '':'src' },
      scripts=['bin/panucci'],
      data_files=data_files,
     )
