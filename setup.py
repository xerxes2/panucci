#!/usr/bin/env python

from distutils.core import setup

setup(name='Panucci',
      version='0.2',
      description='A Resuming Media Player',
      author='Thomas Perl',
      author_email='thp@perli.net',
      url='http://thpinfo.com/2008/panucci/',
      packages=['panucci'],
      package_dir={ '':'src' },
      scripts=['bin/panucci'],
     )
