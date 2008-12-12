#!/usr/bin/env python
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

import gtk
import os.path
import sys
import traceback
import webbrowser

supported_extensions = [ '.mp3', '.ogg', '.flac', '.m4a', '.wav' ]
logging_enabled = False
MAEMO, LINUX = range(2)

def get_platform():
    if os.path.exists('/etc/osso_software_version'):
        return MAEMO
    else:
        return LINUX

platform = get_platform()


if platform == LINUX:
    try:
        import pynotify
        pynotify.init('Panucci')
        have_pynotify = True
    except:
        have_pynotify = False
else:
    import hildon


def is_supported( filepath ):
    filepath, extension = os.path.splitext(filepath)
    return extension.lower() in supported_extensions

def convert_ns(time_int):
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

def detect_filetype( filepath ):
    if len(filepath.split('.')) > 1:
        filename, extension = filepath.rsplit( '.', 1 )
        return extension.lower()

def pretty_filename( filename ):
    filename, extension = os.path.basename(filename).rsplit('.',1)
    return filename.replace('_', ' ')

def open_link(d, url, data):
    webbrowser.open_new(url)

def find_image(filename):
    locations = ['./icons/', '../icons/', '/usr/share/panucci/',
        os.path.dirname(sys.argv[0])+'/../icons/']

    for location in locations:
        if os.path.exists(location+filename):
            return os.path.abspath(location+filename)

def log( msg, *args, **kwargs ):
    global logging_enabled
    if args:
        msg = msg % args

    if logging_enabled:
        print msg

        if kwargs.has_key('exception'):
            traceback.print_exc()

    if kwargs.get('notify', False):
        args = ( msg, title ) if kwargs.has_key('title') else (msg,)
        send_notification( *args )

def send_notification( msg, title='Panucci' ):
    if platform == LINUX and have_pynotify:
        icon = find_image('panucci_64x64.png')
        args = ( title, msg ) if icon is None else ( title, msg, icon )
        notification = pynotify.Notification(*args)
        notification.show()
    elif platform == MAEMO:
        # Note: This won't work if we're not in the gtk main loop
        markup = '<b>%s</b>\n<small>%s</small>' % (title, msg)
        hildon.hildon_banner_show_information_with_markup(
            gtk.Label(''), None, markup )

