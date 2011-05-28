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

import gobject
import gst
import logging

from panucci.backends import base

gobject.threads_init()

class Player(base.BasePlayer):
    """A player that uses Gstreamer for playback"""

    def __init__(self):
        base.BasePlayer.__init__(self)
        self.__log = logging.getLogger('panucci.backends.GStreamerPlayer')
        self._player = None
        self._current_uri = None

    def _get_position_duration(self):
        try:
            pos_int = self._player.query_position(gst.FORMAT_TIME, None)[0]
            dur_int = self._player.query_duration(gst.FORMAT_TIME, None)[0]
        except Exception, e:
            self.__log.exception('Error getting position...')
            pos_int = dur_int = 0

        return pos_int, dur_int

    def _get_state(self):
        if self._player is None:
            return self.STATE_NULL
        else:
            state = self._player.get_state()[1]
            return { gst.STATE_NULL    : self.STATE_STOPPED,
                     gst.STATE_PAUSED  : self.STATE_PAUSED,
                     gst.STATE_PLAYING : self.STATE_PLAYING
                   }.get( state, self.STATE_NULL )

    def _load_media(self, uri):
        self.__setup_player()
        self._player.set_property("uri", uri)
        self._current_uri = uri

    def _pause(self):
        pos, dur = self.get_position_duration()
        self.notify('paused', pos, dur, caller=self.pause)
        self._player.set_state(gst.STATE_PAUSED)
        return pos

    def _play(self):
        if self._current_uri and (self._player or not self._load_media(self._current_uri)):
            self._player.set_state(gst.STATE_PLAYING)
            return True
        else:
            return False

    def _stop(self):
        self.notify('stopped', caller=self.stop)

        if self._player:
            self._player.set_state(gst.STATE_NULL)
            self.set_position_duration(0, 0)
            self._player = None

    def _seek(self, position):
        self.seeking = True
        error = False
        try:
            self._player.seek_simple(gst.FORMAT_TIME, gst.SEEK_FLAG_FLUSH, position)
        except Exception, e:
            self.__log.exception( 'Error seeking' )
            error = True
        self.seeking = False
        return not error

    def __setup_player(self):
        self.__log.debug("Creating playbin-based gstreamer player")
        try:
            self._player = gst.element_factory_make('playbin2', 'player')
        except:
            self._player = gst.element_factory_make('playbin', 'player')
        bus = self._player.get_bus()
        bus.add_signal_watch()
        bus.connect('message', self.__on_message)

    def __on_message(self, bus, message):
        t = message.type
        # self.__log.debug('Got message of type %s', t)

        if t == gst.MESSAGE_EOS:
            self.notify( "eof", caller=self.__on_message )

        elif t == gst.MESSAGE_ERROR:
            err, debug = message.parse_error()
            self.__log.critical( 'Error: %s %s', err, debug )
            self.notify( "error", debug, caller=self.__on_message )

        elif t == gst.MESSAGE_STATE_CHANGED:
            if ( message.src == self._player and
                message.structure['new-state'] == gst.STATE_PLAYING ):
                self.notify('playing', caller=self.__on_message)
