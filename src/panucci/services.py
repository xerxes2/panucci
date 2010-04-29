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
#  from services.py -- Core Services for gPodder
#  Thomas Perl <thp@perli.net>   2007-08-24
#
#  2009-02-13 - nikosapi: made ObservableService more Panucci-esque
#

from __future__ import absolute_import

from logging import getLogger

from panucci import platform

import gobject

class ObservableService(object):
    def __init__(self, signal_names=[], log=None):
        self._log = getLogger('ObservableService') if log is None else log

        self.observers = {}
        for signal in signal_names:
            self.observers[signal] = []

        if not signal_names:
            self._log.warning('No signal names defined...')

    def register(self, signal_name, observer):
        if signal_name in self.observers:
            if not observer in self.observers[signal_name]:
                self.observers[signal_name].append(observer)
                self._log.debug( 'Registered "%s" as an observer for "%s"',
                    observer.__name__, signal_name )
            else:
                self._log.warning(
                    'Observer "%s" is already added to signal "%s"',
                    observer.__name__, signal_name )
        else:
            self._log.warning(
                'Signal "%s" is not available for registration', signal_name )

    def unregister(self, signal_name, observer):
        if signal_name in self.observers:
            if observer in self.observers[signal_name]:
                self.observers[signal_name].remove(observer)
                self._log.debug( 'Unregistered "%s" as an observer for "%s"',
                    observer.__name__, signal_name )
            else:
                self._log.warning(
                    'Observer "%s" could not be removed from signal "%s"',
                    observer.__name__, signal_name )
        else:
            self._log.warning(
                'Signal "%s" is not available for un-registration.',
                signal_name )

    def notify(self, signal_name, *args, **kwargs):
        caller = kwargs.get('caller')
        caller = 'UnknownCaller' if caller is None else caller.__name__
        rtn_value = False

        if signal_name in self.observers:
            self._log.debug(
                'Sending signal "%s" for caller "%s"', signal_name, caller )

            rtn_value = True
            for observer in self.observers[signal_name]:
                rtn_value &= bool(observer( *args ))
        else:
            self._log.warning(
                'Signal "%s" (from caller "%s") is not available '
                'for notification', signal_name, caller )

        return rtn_value


class ForwardingObservableService(ObservableService):
    """ An object that builds on ObservableService which provides a simple
        way to forward/proxy a bunch of signals through an object of this
        type. Ie: This object will call it's notify() method whenever a
        forwarded signal from another object is emitted. """

    def forward( self, from_object, signal_names, caller=None ):
        """ Register signals to be forwarded
              from_object: the object from which the signals will be emitted
              signal_names: a string, list, or dict of signal names
              caller: the caller to be passed to notify()

            To forward a single signal, signal_names can just be a string
            containing the name of the signal.

            To forward many signals, signal_names can be a list of strings.

            If you wish to change the name of the emitted signal (ie. if the
            original object's signal is named "foo-bar" but you want this
            object to emit "foo") you can do so by passing a dict to
            signal_names. This dict must contain string pairs:
            { "new name" : "from-object name", }
        """

        # bail if the from object isn't an ObservableService
        if not isinstance( from_object, ObservableService ):
            self._log.error( "Can't forward signals for "
                              "non-ObservableService type objects")
            return

        signals = {} # final list of signals to registered

        if isinstance( signal_names, str ):
            signals[signal_names] = signal_names

        elif isinstance( signal_names, list ):
            for name in signal_names:
                signals[name] = name

        elif isinstance( signal_names, dict ):
            signals = signal_names

        for to_name, from_name in signals.iteritems():
            from_object.register( from_name, self._forward( to_name, caller ))

    def _forward( self, emitted_signal_name, caller ):
        """ Returns a function which calls notify() with the appropriate
            parameters. """

        def _callback( *args, **kwargs ):
            kwargs["caller"] = caller
            return self.notify( emitted_signal_name, *args, **kwargs )

        return _callback


HEADPHONE_SYS = "/sys/devices/platform/gpio-switch/headphone/state"

class __headphone_watcher(ObservableService):
    """ A small service with one singnal that reports whether or not the
        headphones are connected. Returns True if the headphones are connected,
        False if they're not and None if it's not possible to determine the
        headphone status. """

    signals = [ 'headphone-status-changed', ]

    def __init__(self, sys_file):
        self.__log = getLogger('panucci.serivces.__headphone_watcher')
        ObservableService.__init__(self, self.signals, self.__log)

        self.__is_connected = None

        if platform.MAEMO and not platform.FREMANTLE:
            try:
                self.__sys_file = open( sys_file, 'r' )
                self.__is_connected = self.__get_state_from_fd(self.__sys_file)
                gobject.io_add_watch( self.__sys_file, gobject.IO_PRI,
                                      self.__on_status_changed )
            except IOError:
                self.__log.exception("Can't open headphone status file.")

    @property
    def is_connected(self):
        return self.__is_connected

    def __get_state_from_fd(self, fd):
        fd.seek(0)
        state = fd.read().strip()
        return state == 'connected'

    def __on_status_changed(self, src, cond):
        self.__is_connected = self.__get_state_from_fd( src )
        self.__log.debug(
            'Headphone state changed (is_connected=%s).', self.__is_connected )
        self.notify( 'headphone-status-changed', self.__is_connected,
                     caller=self.__on_status_changed )
        return True

headphone_service = __headphone_watcher(HEADPHONE_SYS)

