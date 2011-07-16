# -*- coding: utf-8 -*-
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

from __future__ import absolute_import

import os.path
from sys import argv
from urllib import quote

def convert_ns(time_int):
    """Convert nanosecond values into strings

    This function should be used to generate
    a string suitable for display in the UI.
    """
    time_int = max( 0, int(time_int) )
    time_int = time_int / 10**9
    time_str = ""
    if time_int >= 3600:
        _hours = time_int / 3600
        time_int = time_int - (_hours * 3600)
        time_str = str(_hours) + ":"
    if time_int >= 600:
        _mins = time_int / 60
        time_int = time_int - (_mins * 60)
        time_str = time_str + str(_mins) + ":"
    elif time_int >= 60:
        _mins = time_int / 60
        time_int = time_int - (_mins * 60)
        time_str = time_str + "0" + str(_mins) + ":"
    else:
        time_str = time_str + "00:"
    if time_int > 9:
        time_str = time_str + str(time_int)
    else:
        time_str = time_str + "0" + str(time_int)

    return time_str

def detect_filetype(filepath):
    """Return the file type (extension) of a file path

    This returns something like "ogg", "mp3", etc..
    """
    filename, extension = os.path.splitext(filepath)
    if extension.startswith('.'):
        extension = extension[1:]
    return extension.lower()

def pretty_filename(filename):
    """Return a prettified version of a filename

    Currently, this removes the extension and
    replaces underscores with spaces.
    """
    filename, extension = os.path.splitext(filename)
    basename = os.path.basename(filename)
    return basename.replace('_', ' ')

def find_data_file(filename):
    bin_dir = os.path.dirname(argv[0])
    locations = [
            os.path.join(bin_dir, '..', 'share', 'panucci'),
            os.path.join(bin_dir, '..', 'icons'),
            os.path.join(bin_dir, '..', 'data'),
            '/opt/panucci',
            os.path.join(bin_dir, '..', 'data/ui/qml'),
    ]

    for location in locations:
        fn = os.path.abspath(os.path.join(location, filename))
        if os.path.exists(fn):
            return fn

def write_config(config):
    _file = open(os.path.expanduser("~/.config/panucci/panucci-noedit.conf"), "w")
    config.write(_file)
    _file.close()

def file_to_url(uri):
    if uri.startswith('/'):
        uri = 'file://' + quote(os.path.abspath(uri))
    return uri
