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

