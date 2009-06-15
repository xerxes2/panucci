# ossohelper.py - Helper to osso functions
#
#  Copyright (c) 2008 INdT - Instituto Nokia de Tecnologia
#
#  This file is part of carman-python.
#  Modified for inclusion in Panucci (June 2009).
#
#  carman-python is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  carman-python is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program.  If not, see <http://www.gnu.org/licenses/>.

import os
import logging

__log = logging.getLogger('panucci.ossohelper')

try:
    import osso
    __osso_imported__ = True
except ImportError:
    __log.warning('osso module not found - are you running on a desktop?')
    __osso_imported__ = False

DEVICE_STATE_NORMAL     = "normal"
OSSO_DEVSTATE_MODE_FILE = "/tmp/.libosso_device_mode_cache"

__osso_context__ = None
__osso_application__ = None
__osso_device_state__ = None

def application_init(app_name, app_version):
    """
    Osso application init.
    """

    global __osso_context__, __osso_device_state__, __osso_application__

    if __osso_imported__:
        if has_osso():
            __log.warning('osso application was already called. Ignoring...')
            return
        try:
            __osso_context__ = osso.Context(app_name, app_version, False)
        except Exception, err:
            __log.warning('osso module found but could not be initialized: %s',
                          err)
            __osso_context__ = None
            return

        try:
            __osso_application__ = osso.Application(__osso_context__)
        except Exception, err:
            __log.warning('error creating osso application: %s' % err)
            __osso_application__ = None

        __log.info( 'osso application init sent - %s v%s', app_name,
                    app_version)
        __osso_device_state__ = osso.DeviceState(__osso_context__)
# application_init

def application_exit():
    """
    Osso application exit.
    """
    if __osso_application__ is not None and __osso_context__ is not None:
        try:
            __osso_application__.close()
            __osso_context__.close()
        except Exception, err:
            __log.warning('application end could not be sent: %s' % err)
        __log.info('osso application end sent')
# application_exit

def application_top(app_name):
    """
    Osso application top.
    """
    if __osso_imported__ and __osso_application__:
        try:
            __osso_application__.application_top(app_name)
        except Exception, err:
            __log.warning( "Error calling application top for %s: %s",
                           app_name, err)
        __log.info('osso application top for %s sent', app_name)

# application_top

def has_osso():
    """
    Return if the osso module was initialized and all objects were created
    without any problem
    """
    return __osso_imported__ and not None in ( __osso_context__, 
                                               __osso_device_state__, 
                                               __osso_application__ )
# has_osso

def display_on():
    """
    Turn on the display
    """
    if __osso_device_state__ is not None:
        __osso_device_state__.display_state_on()
        __osso_device_state__.display_blanking_pause()
        __log.info('osso display on')
# display_on

def display_blanking_pause():
    """
    Keep the backlight on. Should be called every 45 seconds.
    """
    if __osso_device_state__ is not None:
        __osso_device_state__.display_blanking_pause()
        __log.debug('osso blanking screen')
#display_blanking_pause

def get_device_state():
    if __osso_device_state__ is not None:
        cache_file_name = OSSO_DEVSTATE_MODE_FILE + "-" + str(os.getuid())
        try:
            state = os.readlink(cache_file_name)
        except:
            state = None
        if not state:
            __log.debug( "Failure to read device state from %s",
                         cache_file_name)
            state = DEVICE_STATE_NORMAL
        return state
    else:
        return DEVICE_STATE_NORMAL
