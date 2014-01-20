# -*- coding: utf-8 -*-

from __future__ import absolute_import

import os.path
from sys import argv
from urllib import quote

def convert_ns(time_int):
    """Convert nanosecond values into strings
    This function should be used to generate
    a string suitable for display in the UI.
    """
    s,ns = divmod(time_int, 1000000000)
    m,s = divmod(s, 60)

    if m < 60:
        return "%02i:%02i" % (m,s)
    else:
        h,m = divmod(m, 60)
        return "%i:%02i:%02i" % (h,m,s)

def detect_filetype(filepath):
    """Return the file type (extension) of a file path
    This returns something like "ogg", "mp3", etc..
    """
    return filepath.split(".")[-1]

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
            os.path.join(bin_dir, '..', 'share', 'panucci', "icons"),
            os.path.join(bin_dir, '..', 'icons'),
            os.path.join(bin_dir, '..', 'data'),
            os.path.join(bin_dir, '..', 'data/ui'),
            '/opt/panucci',
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
