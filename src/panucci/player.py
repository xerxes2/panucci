# -*- coding: utf-8 -*-
#
# This file is part of Panucci.
# Copyright (c) 2008-2011 The Panucci Project
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

from __future__ import absolute_import

import logging

from panucci.services import ForwardingObservableService
from panucci.dbusinterface import interface
from panucci import util

class PanucciPlayer(ForwardingObservableService):
    """
    A proxy object which adds a layer of abstraction between all the different
    backends. It picks the right backend for the job and forwards signals from
    them.
    """
    signals = [ "playing", "paused", "stopped", "eof" ]

    def __init__(self, config):
        self.__log = logging.getLogger('panucci.player.PanucciPlayer')
        ForwardingObservableService.__init__(self, self.signals, self.__log)
        self.config = config

        if self.config.get("options", "backend") == "gstreamer":
            from panucci.backends.gstreamer import Player
        self.__player = Player()

        self.__initialized = False
        self._start_position = 0

        # Forward the following signals
        self.forward(self.__player, [ "playing", "paused", "stopped", "eof" ], PanucciPlayer)

        #self.__player.register( "playing", self.on_playing )
        self.__player.register( "paused", self.on_paused )
        self.__player.register( "stopped", self.on_stopped )
        self.__player.register( "eof", self.on_stopped )
        self.__player.register( "error", self.on_player_error )

    def __getattr__(self, attr):
        """ If the attribute isn't found in this object, get it from
            the player object. This makes proxying function calls simple
            and transparent.
        """

        if self.__player is not None:
            return getattr(self.__player, attr)
        else:
            self.__log.critical("No player available")
            raise AttributeError

    def on_new_track(self, filepath):
        """ New track callback; loads the new track. """
        if filepath:
            if filepath.startswith('/'):
                filepath = 'file://' + filepath
            self.load_media(filepath)

    def do_seek(self, from_beginning=None, from_current=None, percent=None):
        pos, dur = self.get_position_duration()
        pos_sec = max(0, pos / 10**9)
        dur_sec = max(0, dur / 10**9)

        if self.playing and self.current_uri:
            interface.PlaybackStopped(self._start_position, pos_sec, dur_sec, self.current_uri)

        # Hand over the seek command to the backend
        return self.__player.do_seek(from_beginning, from_current, percent)

    def on_playing(self, seek_to):
        """
        Used to seek to the correct position once the file has started
        playing. This has to be done once the player is ready because
        certain player backends can't seek in any state except playing.
        """
        if seek_to > 0:
            self._seek(seek_to)

        pos, dur = self.get_position_duration()
        pos_sec = pos / 10**9
        dur_sec = dur / 10**9

        interface.PlaybackStarted(pos_sec, self.current_uri)
        self._start_position = pos_sec

    def on_paused(self, *args):
        self.on_stopped_paused()

    def on_stopped(self, *args):
        self.on_stopped_paused()

    def on_stopped_paused(self):
        pos, dur = self.get_position_duration()
        pos_sec = max(0, pos / 10**9)
        dur_sec = max(0, dur / 10**9)
        if self.current_uri:
            interface.PlaybackStopped(self._start_position, pos_sec, dur_sec, self.current_uri)

    def on_stop_requested(self):
        self.stop()

    def on_reset_playlist(self):
        self.stop(True)
        self.__player.reset_position_duration()

    def on_player_error(self, msg):
        self.__log.error("Error: %s", msg)
