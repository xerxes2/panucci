#!/usr/bin/python
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

import logging
from simplegconf import gconf

# If you add a setting _please_ update the schemas file

default_settings = {
    'db_location'       : '~/.panucci.sqlite',
    'last_folder'       : '~',
    'max_recent_files'  : 10,
    'progress_locked'   : False,
    'temp_playlist'     : '~/.panucci.m3u',
    'volume'            : 0.3,
}

class Settings(object):
    __log = logging.getLogger('panucci.settings.Settings')

    def __getattr__(self, key):
        if default_settings.has_key(key):
            return gconf.sget( key, default=default_settings[key] )
        else:
            self.__log.warning('Setting "%s" doesn\'t exist.' % key)

    def __setattr__(self, key, value):
        if default_settings.has_key(key):
            if type(value) == type(default_settings[key]):
                gconf.sset( key, value )
                return True
            else:
                self.__log.warning(
                    'Type of "%s" (%s) does not match default type (%s)',
                    key, type(value), type(default_settings[key]) )
        else:
            self.__log.warning('Setting "%s" doesn\'t exist.', key)

        return False


settings = Settings()

