#!/usr/bin/python
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

import logging
from simplegconf import gconf

# If you add a setting _please_ update the schemas file

default_settings = {
    'db_location'          : '~/.panucci.sqlite',
    'disable_delayed_skip' : False,
    'last_folder'          : '~',
    'max_recent_files'     : 10,
    'progress_locked'      : False,
    'seek_long'            : 60,
    'seek_short'           : 10,
    'skip_delay'           : 0.5,
    'temp_playlist'        : '~/.panucci.m3u',
    'volume'               : 0.3,
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

