#!/usr/bin/env python
#
# This file is part of Panucci.
# Copyright (c) 2008-2010 The Panucci Audiobook and Podcast Player Project
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

from __future__ import absolute_import

import os.path
import logging

try:
    import gconf
except:
    # on the tablet, it's probably in "gnome"
    from gnome import gconf


gconf_dir = '/apps/panucci'

class SimpleGConfClient(gconf.Client):
    """ A simplified wrapper around gconf.Client
        GConf docs: http://library.gnome.org/devel/gconf/stable/
    """

    __type_mapping = { int: 'int', long: 'float', float: 'float',
        str: 'string', bool: 'bool', list: 'list', }

    def __init__(self, directory):
        """ directory is the base directory that we're working in """
        self.__log = logging.getLogger('panucci.simplegconf.SimpleGConfClient')
        self.__directory = directory
        gconf.Client.__init__(self)

        self.add_dir( self.__directory, gconf.CLIENT_PRELOAD_NONE )

    def __get_manipulator_method( self, data_type, operation ):
        """ data_type must be a vaild "type"
            operation is either 'set' or 'get' """

        if self.__type_mapping.has_key( data_type ):
            method = operation + '_' + self.__type_mapping[data_type]
            return getattr( self, method )
        else:
            self.__log.warn('Data type "%s" is not supported.', data_type)
            return lambda x,y=None: None

    def sset( self, key, value ):
        """ A simple set function, no type is required, it is determined
            automatically. 'key' is relative to self.__directory """

        return self.__get_manipulator_method(type(value), 'set')(
            os.path.join(self.__directory, key), value )

    def sget( self, key, data_type=None, default=None ):
        """ A simple get function, data_type or default value is required,
        if default value is given data type will be guessed from it,
        'key' is relative to self.__directory """

        dtype = type(default) if data_type is None else data_type
        if dtype is None:
            self.__log.warn('sget error: data_type or default must be set')
            return

        if self.get( os.path.join(self.__directory, key) ) is None:
            return default
        else:
            return self.__get_manipulator_method(dtype, 'get')(
                os.path.join(self.__directory, key) )

    def snotify( self, callback ):
        """ Set a callback to watch self.__directory """
        return self.notify_add( self.__directory, callback )

gconf = SimpleGConfClient( gconf_dir )

