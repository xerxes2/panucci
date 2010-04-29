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
# Documentation for osso-media-server's dbus api is very sparse.
# We used atabake's oms_backend.py since they found a good portion of the
# available member functions. Anything else was found by playing files using
# the nokia media player and watching dbus-monitor.
#

from __future__ import absolute_import

import dbus
import logging

from panucci.backends import base

class ossoPlayer(base.BasePlayer):
    """
    A player which uses osso-media-server for playback (Maemo-specific)
    """

    SERVICE_NAME         = "com.nokia.osso_media_server"
    OBJECT_PATH          = "/com/nokia/osso_media_server"
    AUDIO_INTERFACE_NAME = "com.nokia.osso_media_server.music"

    def __init__(self):
        base.BasePlayer.__init__(self)
        self.__log = logging.getLogger("panucci.backends.ossoPlayer")
        self.__log.debug("Initialized ossoPlayer backend")

        self.__state = self.STATE_NULL # manually keep track of player state
        self.audio_proxy = self._init_dbus()
        self._init_signals()

    def _init_dbus(self):
        session_bus = dbus.SessionBus()

        # Get the osso-media-player proxy object
        oms_object = session_bus.get_object( self.SERVICE_NAME,
                                             self.OBJECT_PATH,
                                             introspect=False,
                                             follow_name_owner_changes=True )
        # Use the audio interface
        oms_audio_interface = dbus.Interface( oms_object,
                                              self.AUDIO_INTERFACE_NAME )

        return oms_audio_interface

    def _init_signals(self):
        error_signals = {
            "no_media_selected":            base.BASE_ERROR_NO_MEDIA,
            "file_not_found":               base.BASE_ERROR_FILE_NOT_FOUND,
            "type_not_found":               base.BASE_ERROR_UNSUPPORTED,
            "unsupported_type":             base.BASE_ERROR_UNSUPPORTED,
            "gstreamer":                    base.BASE_ERROR_BACKEND,
            "dsp":                          base.BASE_ERROR_HARDWARE,
            "device_unavailable":           base.BASE_ERROR_HARDWARE,
            "corrupted_file":               base.BASE_ERROR_BAD_FILE,
            "out_of_memory":                base.BASE_ERROR_HARDWARE,
            "audio_codec_not_supported":    base.BASE_ERROR_UNSUPPORTED,
        }

        # Connect status signals
        self.audio_proxy.connect_to_signal( "state_changed",
                                            self._on_state_changed )
        self.audio_proxy.connect_to_signal( "end_of_stream",
                                            lambda x: self.notify("eof") )

        # Connect error signals
        def e(err): return lambda *y: self.notify("error",err,caller=ossoPlayer)
        for error,msg in error_signals.iteritems():
            self.audio_proxy.connect_to_signal( error, e(msg) )

    def _on_state_changed(self, state):
        state_map = { "playing": self.STATE_PLAYING,
                      "paused":  self.STATE_PAUSED,
                      "stopped": self.STATE_STOPPED
                    }

        self.__state = state_map.get( state, self.STATE_NULL )

        if state in state_map.keys():
            if state == "paused":
                pos, dur = self.get_position_duration()
                self.notify( "paused", pos, dur, caller=ossoPlayer )
            else:
                self.notify( state, caller=ossoPlayer )
        else:
            self.__log.info("Unknown state: %s", state)

    def get_state(self):
        return self.__state

    def load_media(self, uri):
        self.audio_proxy.set_media_location(uri)

    def pause(self):
        if self.playing:
            # cache the current position/duration
            self.get_position_duration()
            self.audio_proxy.pause()

    def play(self):
        self.audio_proxy.play()

    def stop(self):
        self.audio_proxy.stop()

    def _get_position_duration(self):
        pos_info = self.audio_proxy.get_position()

        if isinstance(pos_info, tuple):
            pos, dur = pos_info
            return int(pos)*10**6, int(dur)*10**6
        else:
            return 0,0

    def _seek(self, position):
        self.audio_proxy.seek( dbus.Int32(1), dbus.Int32(position/10**6) )

