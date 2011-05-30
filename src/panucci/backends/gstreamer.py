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
        self.__player = None
        # Workaround for weird bug
        self.initial_pause_position = True

    def _get_position_duration(self):
        try:
            if self.initial_pause_position == True:
                pos_int = 0
            else:
                pos_int = self.__player.query_position(gst.FORMAT_TIME, None)[0]
            dur_int = self.__player.query_duration(gst.FORMAT_TIME, None)[0]
        except Exception, e:
            self.__log.exception('Error getting position...')
            pos_int = dur_int = 0

        return pos_int, dur_int

    def _get_state(self):
        if self.__player is None:
            return self.STATE_NULL
        else:
            state = self.__player.get_state()[1]
            return { gst.STATE_NULL    : self.STATE_STOPPED,
                     gst.STATE_PAUSED  : self.STATE_PAUSED,
                     gst.STATE_PLAYING : self.STATE_PLAYING
                   }.get( state, self.STATE_NULL )

    def _load_media(self, uri):
        self.__setup_player()
        self.__player.set_property("uri", uri)
        self.__player.set_state(gst.STATE_PAUSED)
        self.current_uri = uri
        self.initial_pause_position = True

    def _pause(self):
        self.__player.set_state(gst.STATE_PAUSED)
        pos, dur = self.get_position_duration()
        self.notify('paused', pos, dur, caller=self.pause)
        return pos

    def _play(self):
        if self.current_uri and (self.__player or not self._load_media(self.current_uri)):
            self.__player.set_state(gst.STATE_PLAYING)
            self.initial_pause_position = False
            return True
        else:
            return False

    def _stop(self, player):
        self.notify('stopped', caller=self.stop)
        if self.__player:
            self.__player.set_state(gst.STATE_NULL)
            self.set_position_duration(0, 0)
            self.initial_pause_position = True
            self.__player.set_state(gst.STATE_PAUSED)
            if player:
                self.__player.set_state(gst.STATE_NULL)
                self.__player = None

    def _seek(self, position):
        self.seeking = True
        error = False
        try:
            self.__player.seek_simple(gst.FORMAT_TIME, gst.SEEK_FLAG_FLUSH, position)
        except Exception, e:
            self.__log.exception( 'Error seeking' )
            error = True
        self.seeking = False
        self.initial_pause_position = False
        return not error

    def __setup_player(self):
        self.__log.debug("Creating playbin-based gstreamer player")
        if self.__player:
            self.__player.set_state(gst.STATE_NULL)
        try:
            self.__player = gst.element_factory_make('playbin2', 'player')
        except:
            self.__player = gst.element_factory_make('playbin', 'player')
        bus = self.__player.get_bus()
        bus.add_signal_watch()
        bus.connect('message', self.__on_message)

    def __on_message(self, bus, message):
        t = message.type
        if t == gst.MESSAGE_EOS:
            self.notify( "eof", caller=self.__on_message )
        elif t == gst.MESSAGE_ERROR:
            err, debug = message.parse_error()
            self.__log.critical( 'Error: %s %s', err, debug )
            self.notify( "error", debug, caller=self.__on_message )
        elif t == gst.MESSAGE_STATE_CHANGED:
            if ( message.src == self.__player and
                message.structure['new-state'] == gst.STATE_PLAYING ):
                self.notify('playing', caller=self.__on_message)
