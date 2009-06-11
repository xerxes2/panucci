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
    signals = [ 'playing', 'paused', 'stopped' ]

    def __init__(self):
        self.__log = logging.getLogger('panucci.player.panucciPlayer')
        ObservableService.__init__(self, self.signals, self.__log)
        interface.register_player(self)

        self.playlist = Playlist()
        self.playlist.register( 'new-track-playing', self.on_new_track )
        self.playlist.register( 'seek-requested', self.do_seek )
        self.playlist.register( 'stop-requested', self.stop )
        settings.register( 'volume_changed', self.__set_volume_level )

        self.__initial_seek = False # have we preformed the initial seek?
        self.seeking = False        # are we seeking?

        self.__player = None
        self.__volume_control = None
        self.__volume_multiplier = 1

        self.time_format = gst.Format(gst.FORMAT_TIME)

    def init(self, filepath=None):
        """ This should be called by the UI once it has initialized """
        if filepath is not None and self.playlist.load( filepath ):
            self.play()
        else:
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
        pos, dur = self.get_position_duration()
        self.notify('paused', pos, dur, caller=self.pause)
        self.__player.set_state(gst.STATE_PAUSED)
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

    def __setup_player(self):
        filetype = self.playlist.get_current_filetype()
        filepath = self.playlist.get_current_filepath()

        if None in [ filetype, filepath ]:
            self.__player = None
            return False
        
        # On maemo use software decoding to workaround some bugs their gst:
        # 1. Weird volume bugs in playbin when playing ogg or wma files
        # 2. When seeking the DSPs sometimes lie about the real position info
        if util.platform == util.MAEMO:
            self.__player = gst.Pipeline('player')
            src = gst.element_factory_make('gnomevfssrc', 'src')
            decoder = gst.element_factory_make('decodebin', 'decoder')
            convert = gst.element_factory_make('audioconvert', 'convert')
            resample = gst.element_factory_make('audioresample', 'resample')
            sink = gst.element_factory_make('dsppcmsink', 'sink')
            
            self.__filesrc = src # pointer to the main source element
            
            # The volume is set using the dsppcmsink's volume control 
            # which takes an integer value from 0 to 65535
            self.__volume_control = sink
            self.__volume_multiplier = 2**16 - 1
            
            # Add the various elements to the player pipeline
            self.__player.add( src, decoder, convert, resample, sink )
            
            # Link what can be linked now, the decoder->convert happens later
            gst.element_link_many( src, decoder )
            gst.element_link_many( convert, resample, sink )
            
            # We can't link the two halves of the pipeline until it comes
            # time to start playing, this singal lets us know when it's time.
            # This is because the output from decoder can't be determined until
            # decoder knows what it's decoding.
            decoder.connect( 'pad-added',
                             self.__on_decoder_pad_added,
                             convert.get_pad('sink') )
        else:
            # This is for *ahem* "normal" versions of gstreamer
            self.__player = gst.element_factory_make('playbin', 'player')
            # Isn't playbin simple :)
            self.__filesrc = self.__volume_control = self.__player
            self.__volume_multiplier = 1.
        
        self.__set_uri_to_be_played( 'file://' + filepath )

        bus = self.__player.get_bus()
        bus.add_signal_watch()
        bus.connect('message', self.__on_message)
        self.__set_volume_level( settings.volume )

        return True
    
    def __on_decoder_pad_added(self, decoder, src_pad, sink_pad):
        # link the decoder's new "src_pad" to "sink_pad"
        src_pad.link( sink_pad )
    
    def __get_volume_level(self):
        if self.__volume_control is not None:
            return self.__volume_control.get_property(
                'volume') / float(self.__volume_multiplier)

    def __set_volume_level(self, value):
        assert  0 <= value <= 1

        if self.__volume_control is not None:
            vol = value * self.__volume_multiplier
            vol = int(vol) if util.platform == util.MAEMO else float(vol)
            self.__volume_control.set_property( 'volume', vol )
    
    def __set_uri_to_be_played( self, uri ):
        # Sets the right property depending on the platform of self.__filesrc
        if self.__player is not None:
            prop = 'location' if util.platform == util.MAEMO else 'uri'
            self.__filesrc.set_property( prop, uri )
    
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
            self.__log.debug('do_seek: Seeking to: %d', position)
            self.__seek(position)
            return position, duration
        else:
            self.__log.debug('do_seek: Could not seek.')

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

