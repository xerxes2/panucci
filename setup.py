#!/usr/bin/env python

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
