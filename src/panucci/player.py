#!/usr/bin/env python
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
#

from __future__ import absolute_import

import logging

from panucci.playlist import Playlist
from panucci.services import ForwardingObservableService
from panucci.dbusinterface import interface
from panucci.backends import gstreamer

from panucci import util

class PanucciPlayer(ForwardingObservableService):
    """
    A proxy object which adds a layer of abstraction between all the different
    backends. It picks the right backend for the job and forwards signals from
    them.
    """
    signals = [ "playing", "paused", "stopped", "eof" ]

    def __init__(self, player):
        self.__log = logging.getLogger('panucci.player.PanucciPlayer')
        ForwardingObservableService.__init__(self, self.signals, self.__log)
        self.__player = player
        self.__initialized = False
        self._start_position = 0
        self._is_playing = False

        # Forward the following signals
        self.forward( self.__player,
                      [ "playing", "paused", "stopped", "eof" ],
                      PanucciPlayer )

        self.__player.register( "playing", self.on_playing )
        self.__player.register( "paused", self.on_stopped )
        self.__player.register( "stopped", self.on_stopped )
        #self.__player.register( "eof", self.on_eof )
        self.__player.register( "error", self.on_player_error )

        self.playlist = Playlist()
        self.playlist.register( 'new-track-loaded', self.on_new_track )
        self.playlist.register( 'seek-requested', self.do_seek )
        self.playlist.register( 'stop-requested', self.on_stop_requested )
        self.playlist.register( 'reset-playlist', self.on_reset_playlist )

        # Register the d-bus interface only once we're ready
        interface.register_player(self)

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

    def add_bookmark_at_current_position( self, label=None ):
        """ Adds a bookmark at the current position

            Returns: (bookmark lable string, position in nanoseconds)
        """

        default_label, position = player.get_formatted_position()
        label = default_label if label is None else label
        self.playlist.save_bookmark( label, position )
        self.__log.info('Added bookmark: %s - %d', label, position)
        return label, position

    def get_formatted_position(self, pos=None):
        """ Gets the current position and converts it to a human-readable str.

            Returns: (bookmark lable string, position in nanoseconds)
        """

        if pos is None:
            (pos, dur) = self.get_position_duration()

        text = util.convert_ns(pos)
        return (text, pos)

    def init(self, filepath=None):
        """ Start playing the current file in the playlist or a custom file.
            This should be called by the UI once it has initialized.

            Params: filepath is an optional filepath to the first file that
                    should be loaded/played
            Returns: Nothing
        """

        if filepath is None or not self.playlist.load( filepath ):
            self.playlist.load_last_played()
        else:
            self.play()

    def on_new_track(self):
        """ New track callback; stops the player and starts the new track. """

        if self.playlist.current_filepath is not None:
            filepath = self.playlist.current_filepath
            if filepath.startswith('/'):
                filepath = 'file://' + filepath
            self.load_media(filepath)

            # This is just here to prevent the player from starting to play
            # when it is first opened. The first time this function is called it
            # doesn't run self.play(), but otherwise it will.
            if self.__initialized:
                self.play()

        self.__initialized = True

    def do_seek(self, from_beginning=None, from_current=None, percent=None):
        pos, dur = self.get_position_duration()
        pos_sec = max(0, pos / 10**9)
        dur_sec = max(0, dur / 10**9)

        if self._is_playing and self.current_file:
            interface.PlaybackStopped(self._start_position, pos_sec, dur_sec, self.current_file)
            self._is_playing = False

        # Hand over the seek command to the backend
        return self.__player.do_seek(from_beginning, from_current, percent)

    def on_playing(self):
        """
        Used to seek to the correct position once the file has started
        playing. This has to be done once the player is ready because
        certain player backends can't seek in any state except playing.
        """
        seek = self.playlist.play()
        if seek > 0:
            self._seek(seek)

        pos, dur = self.get_position_duration()
        pos_sec = pos / 10**9
        dur_sec = dur / 10**9

        interface.PlaybackStarted(pos_sec, self.current_file)
        self._start_position = pos_sec
        self._is_playing = True

    def on_stopped(self, *args):
        pos, dur = self.get_position_duration()
        pos_sec = max(0, pos / 10**9)
        dur_sec = max(0, dur / 10**9)
        if self.current_file is not None:
            interface.PlaybackStopped(self._start_position, pos_sec, dur_sec, self.current_file)
        self._is_playing = False

    def on_eof(self, *args):
        self.playlist.next()

    def play_next(self):
        self.playlist.next()

    def play_prev(self):
        self.playlist.prev()

    @property
    def current_file(self):
        return self.playlist.current_filepath

    def on_stop_requested(self):
        self.playlist.stop( self.get_position_duration()[0] )
        self.stop()
        self._is_playing = False

    def on_reset_playlist(self):
        self.on_stop_requested()
        self.__player.reset_position_duration()

    def on_player_error(self, msg):
        self.__log.error("Error: %s", msg)

    def quit(self):
        """ Called when the application exits """
        self.on_stop_requested()
        self.playlist.quit()

# there should only ever be one panucciPlayer object
player = PanucciPlayer(gstreamer.GStreamerPlayer())
