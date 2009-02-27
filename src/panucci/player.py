#!/usr/bin/env python
#
# This file is part of Panucci.
# Copyright (c) 2008-2009 The Panucci Audiobook and Podcast Player Project
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

import logging

import pygst
pygst.require('0.10')
import gst

from playlist import Playlist
from settings import settings
from services import ObservableService
from dbusinterface import interface

import util

PLAYING, PAUSED, STOPPED, NULL = range(4)

class panucciPlayer(ObservableService):
    """ """
    signals = ['playing', 'paused', 'stopped', 'end_of_playlist']

    def __init__(self):
        self.__log = logging.getLogger('panucci.player.panucciPlayer')
        ObservableService.__init__(self, self.signals, self.__log)
        interface.register_player(self)

        self.playlist = Playlist()
        self.playlist.register( 'new_track', self.on_new_track )

        self.__initial_seek = False # have we preformed the initial seek?
        self.seeking = False        # are we seeking?

        self.__player = None
        self.__volume_control = None
        self.__volume_multiplier = 1

        # Placeholder functions, these are generated dynamically
        self.get_volume_level = lambda: 0
        self.set_volume_level = lambda x: 0

        self.time_format = gst.Format(gst.FORMAT_TIME)

    def init(self, load_last_played=True):
        """ This should be called by the UI once it has initialized """
        if load_last_played:
            self.playlist.load_last_played()

    def play(self):
        have_player = self.__player is not None
        if have_player or self.__setup_player():
            self.notify('playing', caller=self.play)
            self.__initial_seek = have_player
            self.__player.set_state(gst.STATE_PLAYING)
            return True
        else:
            # should something happen here? perhaps self.stop()?
            return False

    def pause(self):
        self.notify('paused', caller=self.pause)
        self.__player.set_state(gst.STATE_PAUSED)
        pos, dur = self.get_position_duration()
        self.playlist.pause(pos)

    def play_pause_toggle(self):
        self.pause() if self.playing else self.play()

    def stop(self, save_resume_point=True):
        self.notify('stopped', caller=self.stop)

        if self.__player is not None:
            position_string, position = self.get_formatted_position()
            self.playlist.stop(position, save_resume_point)
            self.__player.set_state(gst.STATE_NULL)
            self.__player = None

    @property
    def playing(self):
        return self.get_state() == PLAYING

    def get_state(self):
        if self.__player is None:
            return NULL
        else:
            state = self.__player.get_state()[1]
            return { gst.STATE_NULL    : STOPPED,
                     gst.STATE_PAUSED  : PAUSED,
                     gst.STATE_PLAYING : PLAYING }.get( state, NULL )

    def play_file(self, filepath):
        self.stop()
        self.playlist.load(filepath)
        self.play()

    def __setup_player(self):
        filetype = self.playlist.get_current_filetype()
        filepath = self.playlist.get_current_filepath()

        if None in [ filetype, filepath ]:
            self.__player = None
            return False

        if filetype.startswith('ogg') and util.platform == util.MAEMO:
            self.__log.info( 'Using OGG workaround, I hope this works...' )

            self.__player = gst.Pipeline('player')
            source = gst.element_factory_make('gnomevfssrc', 'file-source')

            try:
                audio_decoder = gst.element_factory_make(
                    'tremor', 'vorbis-decoder' )
            except Exception, e:
                self.__log.exception( util.notify(
                    'No ogg decoder available, install the "mogg" package.',
                    title='Missing Decoder.' ))
                self.__player = None
                return False

            self.__volume_control = gst.element_factory_make('volume','volume')
            audiosink = gst.element_factory_make('dsppcmsink', 'audio-output')

            self.__player.add(
                source, audio_decoder, self.__volume_control, audiosink )
            gst.element_link_many(
                source, audio_decoder, self.__volume_control, audiosink )

            source.set_property( 'location', 'file://' + filepath )
        else:
            # Workaround for volume on maemo, they use a 0 to 10 scale
            self.__volume_multiplier = int(util.platform == util.MAEMO)*10 or 1
            self.__log.info( 'Using plain-old playbin.' )
            self.__player = gst.element_factory_make('playbin', 'player')
            self.__volume_control = self.__player
            self.__player.set_property( 'uri', 'file://' + filepath )

        bus = self.__player.get_bus()
        bus.add_signal_watch()
        bus.connect('message', self.__on_message)

        self.volume_level = settings.volume
        return True

    def __get_volume_level(self, volume_control, divisor=1):
        if self.__volume_control is not None:
            vol = self.__volume_control.get_property(
                'volume') / float(self.__volume_multiplier)
            return vol
        else:
            return settings.volume

    def __set_volume_level(self, value):
        assert  0 <= value <= 1

        if self.__volume_control is not None:
            self.__volume_control.set_property(
                'volume', value * float(self.__volume_multiplier))

        settings.volume = value

    volume_level = property( __get_volume_level, __set_volume_level )

    def get_formatted_position(self, pos=None):
        if pos is None:
            if self.playing:
                (pos, dur) = self.get_position_duration()
            else:
                pos = self.playlist.get_current_position()
        text = util.convert_ns(pos)
        return (text, pos)

    def get_position_duration(self):
        """ returns [ current position, total duration ] """
        try:
            pos_int = self.__player.query_position(self.time_format, None)[0]
            dur_int = self.__player.query_duration(self.time_format, None)[0]
        except Exception, e:
            #self.__log.exception('Error getting position...')
            pos_int = dur_int = 0
        return pos_int, dur_int

    def do_seek(self, from_beginning=None, from_current=None, percent=None ):
        """ Takes one of the following keyword arguments:
                from_beginning=n: seek n nanoseconds from the start of the file
                from_current=n: seek n nanoseconds from the current position
                percent=n: seek n percent from the beginning of the file
        """
        error = False
        position, duration = self.get_position_duration()

        # if position and duration are 0 then player_get_position caught an
        # exception. Therefore self.__player isn't ready to be seeking.
        if not ( position or duration ) or self.__player is None:
            error = True
        else:
            if from_beginning is not None:
                assert from_beginning >= 0
                position = min( from_beginning, duration )
            elif from_current is not None:
                position = max( 0, min( position+from_current, duration ))
            elif percent is not None:
                assert 0 <= percent <= 1
                position = int(duration*percent)
            else:
                self.__log.warning('No seek parameters specified.')
                error = True

        if not error:
            self.__seek(position)
            return position, duration

        return False

    def __seek(self, position):
        # Don't use this, use self.do_seek instead
        self.seeking = True
        error = False

        try:
            self.__player.seek_simple(
                self.time_format, gst.SEEK_FLAG_FLUSH, position )
        except Exception, e:
            self.__log.exception( 'Error seeking' )
            error = True

        self.seeking = False
        return not error

    def on_new_track(self):
        self.stop(save_resume_point=False)
        self.play()

    def __on_message(self, bus, message):
        t = message.type
        # self.__log.debug('Got message of type %s', t)

        if t == gst.MESSAGE_EOS and not self.playlist.next():
            self.stop(save_resume_point=False)
            self.notify( 'end_of_playlist', caller=self.__on_message )

        elif t == gst.MESSAGE_ERROR:
            err, debug = message.parse_error()
            self.__log.critical( 'Error: %s %s', err, debug )
            self.stop()

        elif t == gst.MESSAGE_STATE_CHANGED:
            if ( message.src == self.__player and
                message.structure['new-state'] == gst.STATE_PLAYING ):

                if not self.__initial_seek:
                    # This only gets called when the file is first loaded
                    pause_time = self.playlist.play()
                    # don't seek if position is 0
                    if pause_time > 0:
                        self.__log.info('Seeking to %d' % pause_time)
                        # seek manually; on maemo it is sometimes impossible
                        # to query the player this early in the process
                        self.__seek(pause_time)

                    self.__initial_seek = True

    def quit(self):
        """ Called when the application exits """
        self.stop()
        self.playlist.quit()

# there should only ever be one panucciPlayer object
player = panucciPlayer()

