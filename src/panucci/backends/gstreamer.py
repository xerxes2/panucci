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

import gst
import logging

import panucci

from panucci import util

from panucci.backends import base

class GStreamerPlayer(base.BasePlayer):
    """ A player that uses Gstreamer for playback """

    def __init__(self):
        base.BasePlayer.__init__(self)
        self.__log = logging.getLogger('panucci.backends.GStreamerPlayer')

        # have we preformed the initial seek?
        self.__initial_seek_completed = False

        self._player = None
        self._filesrc = None
        self._filesrc_property = None
        self._time_format = gst.Format(gst.FORMAT_TIME)
        self._current_filetype = None

    def _get_position_duration(self):
        try:
            pos_int = self._player.query_position(self._time_format,None)[0]
            dur_int = self._player.query_duration(self._time_format,None)[0]
        except Exception, e:
            self.__log.exception('Error getting position...')
            pos_int = dur_int = 0

        return pos_int, dur_int

    def get_state(self):
        if self._player is None:
            return self.STATE_NULL
        else:
            state = self._player.get_state()[1]
            return { gst.STATE_NULL    : self.STATE_STOPPED,
                     gst.STATE_PAUSED  : self.STATE_PAUSED,
                     gst.STATE_PLAYING : self.STATE_PLAYING
                   }.get( state, self.STATE_NULL )

    def pause(self):
        pos, dur = self.get_position_duration()
        self.notify('paused', pos, dur, caller=self.pause)
        self._player.set_state(gst.STATE_PAUSED)
        return pos

    def play(self):
        have_player = self._player is not None
        
        # Don't think this is needed
        #if have_player or self.__setup_player():
        if have_player:
            self._initial_seek_completed = have_player
            self._player.set_state(gst.STATE_PLAYING)
            return True
           
        else:
            # should something happen here? perhaps self.stop()?
            return False

    def stop(self):
        self.notify('stopped', caller=self.stop)

        if self._player is not None:
            position, duration = self.get_position_duration()
            self._player.set_state(gst.STATE_NULL)
            self._player = None

    def stop_end_of_playlist(self):
        self.notify('stopped', caller=self.stop)

        if self._player is not None:
            #position, duration = self.get_position_duration()
            self._player.set_state(gst.STATE_NULL)

    def _seek(self, position):
        self.seeking = True
        error = False

        try:
            self._player.seek_simple(
                self._time_format, gst.SEEK_FLAG_FLUSH, position )
        except Exception, e:
            self.__log.exception( 'Error seeking' )
            error = True

        self.seeking = False
        return not error

    def __setup_player(self):
        if self._setup_player(self._current_filetype):
            bus = self._player.get_bus()
            bus.add_signal_watch()
            bus.connect('message', self.__on_message)
            return True

        return False

    def _setup_player(self, filetype=None):
        self.__log.debug("Creating playbin-based gstreamer player")
        try:
            self._player = gst.element_factory_make('playbin2', 'player')
        except:
            self._player = gst.element_factory_make('playbin', 'player')
        self._filesrc = self._player
        self._filesrc_property = 'uri'
        return True

    def _on_decoder_pad_added(self, decoder, src_pad, sink_pad):
        # link the decoder's new "src_pad" to "sink_pad"
        src_pad.link( sink_pad )

    def load_media( self, uri ):
        filetype = util.detect_filetype(uri)

        if filetype != self._current_filetype or self._player is None:
            self.__setup_player()

        if self._player is not None:
            self._filesrc.set_property( self._filesrc_property, uri )

        self._current_filetype = filetype

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
