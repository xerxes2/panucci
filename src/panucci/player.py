#!/usr/bin/env python

import logging

import pygst
pygst.require('0.10')
import gst

from playlist import Playlist
from settings import settings
from services import ObservableService
import dbusinterface
running_on_tablet=False
short_seek = 10
long_seek = 60

PLAYING, PAUSED, STOP, NULL = range(4)

class panucciPlayer(ObservableService):
    """ """
    signals = [ 'playing', 'paused', 'stopped', 'new_track' ]

    def __init__(self):
        self.__log = logging.getLogger('panucci.player.panucciPlayer')
        #dbusinterface.init_dbus(self)
        ObservableService.__init__(self, self.signals, self.__log)

        self.playlist = Playlist()
        self.__initial_seek = False # have we preformed the initial seek?
        self.__player = None
        self.__volume_control = None

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
        pos, dur = self.__player_get_position()
        self.playlist.pause(pos)

    def stop(self, save_resume_point=True)):
        self.notify('stopped', caller=self.stop)

        if self.__player is not None:
            if save_resume_point:
                position_string, position = self.get_position()
                self.playlist.stop(position)

            self.__player.set_state(gst.STATE_NULL)
            self.__player = None

    @property
    def playing(self):
        return self.get_state() == PLAYING

    def get_state(self):
        if self.__player is None:
            return NULL
        else:
            state = self.__player.get_state()
            return { gst.STATE_NULL    : STOPPED,
                     gst.STATE_PAUSED  : PAUSED,
                     gst.STATE_PLAYING : PLAYING }.get_state( state, NULL )

    def __setup_player(self):
        filetype = self.playlist.get_current_filetype()
        filepath = self.playlist.get_current_filepath()

        if None in [ filetype, filepath ]:
            self.__player = None
            return False

        if filetype.startswith('ogg') and running_on_tablet:
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

            self.get_volume_level = lambda : self.__get_volume_level(
                self.__volume_control )
            self.set_volume_level = lambda x: self.__set_volume_level(
                x, self.__volume_control )

            source.set_property( 'location', 'file://' + filepath )
        else:
            self.__log.info( 'Using plain-old playbin.' )

            self.__player = gst.element_factory_make('playbin', 'player')

            # Workaround for volume on maemo, they use a 0 to 10 scale
            div = int(running_on_tablet)*10 or 1
            self.get_volume_level = lambda : self.__get_volume_level(
                self.__player, div )
            self.set_volume_level = lambda x: self.__set_volume_level(
                x, self.__player, div )

            self.__player.set_property( 'uri', 'file://' + filepath )

        bus = self.__player.get_bus()
        bus.add_signal_watch()
        bus.connect('message', self.__on_message)

        #self.set_volume_level(self.get_volume())
        return True

    def __get_volume_level(self, volume_control, divisor=1):
        vol = volume_control.get_property('volume') / float(divisor)
        assert 0 <= vol <= 1
        return vol

    def __set_volume_level(self, value, volume_control, multiplier=1):
        assert  0 <= value <= 1
        volume_control.set_property('volume', value * float(multiplier))

    def get_position(self, pos=None):
        if pos is None:
            if self.playing:
                (pos, dur) = self.__player_get_position()
            else:
                pos = self.playlist.get_current_position()
        text = util.convert_ns(pos)
        return (text, pos)

    def __player_get_position(self):
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
        self.want_to_seek = True
        error = False

        position, duration = self.__player_get_position()
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
            # Preemptively update the progressbar to make seeking smoother
            self.set_progress_callback( position, duration )
            self.__seek(position)

        self.want_to_seek = False
        return not error

    def __seek(self, position):
        # Don't use this, use self.do_seek instead
        try:
            self.__player.seek_simple(
                self.time_format, gst.SEEK_FLAG_FLUSH, position )
            return True
        except Exception, e:
            self.__log.exception( 'Error seeking' )
            return False

    def __on_message(self, bus, message):
        t = message.type
        self.__log.debug('Got message of type %s', t)

        if t == gst.MESSAGE_EOS:
            self.stop(save_resume_point=False)
            if self.playlist.next():
                self.play()
            else:
                self.stop()

        elif t == gst.MESSAGE_ERROR:
            err, debug = message.parse_error()
            self.__log.critical( 'Error: %s %s', err, debug )
            self.stop_playing()

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

