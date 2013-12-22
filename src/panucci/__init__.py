# -*- coding: utf-8 -*-

from __future__ import absolute_import

import os.path

__version__ = '0.99.4.4'

HOME = os.path.expanduser('~/.config/panucci')

if not os.path.exists(HOME):
    import os
    os.makedirs(HOME)

SETTINGS_FILE = os.path.join(HOME, 'panucci.conf')
DATABASE_FILE = os.path.join(HOME, 'panucci.sqlite')
PLAYLIST_FILE = os.path.join(HOME, 'panucci.m3u')
LOGFILE = os.path.join(HOME, 'panucci.log')
THEME_FILE = os.path.join(HOME, 'theme.conf')

EXTENSIONS = ('mp2', 'mp3', 'mp4', 'ogg', 'm4a', 'wav', 'flac', 'opus')
