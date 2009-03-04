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
import os.path

from simplegconf import gconf
from services import ObservableService

SIGNAL_NAME_SUFFIX = '_changed'

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

class Settings(ObservableService):
    """ A settings manager for Panucci. A signal is emitted when any 
        setting is changed; signal names are devised as follows:
            setting_name + SIGNAL_NAME_SUFFIX 

        The signal prototype is: def callback( new_value )"""

    def __init__(self):
        self.__log = logging.getLogger('panucci.settings.Settings')
        signals = [ k + SIGNAL_NAME_SUFFIX for k in default_settings.keys() ]
        ObservableService.__init__( self, signals, log=self.__log )

        gconf.snotify( self.__on_directory_changed )

    def __getattr__(self, key):
        if default_settings.has_key(key):
            return gconf.sget( key, default=default_settings[key] )
        else:
            self.__log.warning('Setting "%s" doesn\'t exist.' % key)
            raise AttributeError

    def __setattr__(self, key, value):
        if default_settings.has_key(key):
            if type(value) == type(default_settings[key]):
                # Don't set the value if it's the same as it used to be
                if getattr(self, key) != value:
                    gconf.sset( key, value )

                return True
            else:
                self.__log.warning(
                    'Type of "%s" (%s) does not match default type (%s)',
                    key, type(value).__name__,
                    type(default_settings[key]).__name__ )
        else:
            object.__setattr__( self, key, value )
            self.__log.warning('Setting "%s" doesn\'t exist.', key)

        return False

    def __on_directory_changed(self, client, connection_id, entry, args):
        directory, key = os.path.split(entry.get_key())
        new_value = getattr(self, key)
        self.__log.debug('gconf key %s changed to: %s', key, new_value)
        self.notify( key + SIGNAL_NAME_SUFFIX, new_value,
            caller=self.__on_directory_changed )

    def attach_checkbutton(self, button, setting):
        button.connect(
            'toggled', lambda w: setattr( self, setting, w.get_active()) )
        self.register(
            setting + SIGNAL_NAME_SUFFIX, lambda v: button.set_active(v) )
        button.set_active( getattr(self, setting) )

settings = Settings()

