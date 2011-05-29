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

import panucci
from panucci import services

class BasePlayer(services.ObservableService):
    """ The player base class, this can't be used directly because most of
        the important functions need to be filled in by subclasses.
    """

    """
    Signals
        playing             : ( )
          Issued when the player starts playing
        paused              : ( )
           Issued when the player pauses
        stopped             : ( )
           Issued when the player stops
        eof                 : ( )
           Issued at the end of a file
        error               : ( error_code, error_string )
           Issued when an error occurs. "error_code" is a unique code for a
           specific error, "error_string" is a human-readable string that
           describes the error.
    """
    signals = [ 'playing', 'paused', 'stopped', 'eof', 'error' ]
    STATE_PLAYING, STATE_PAUSED, STATE_STOPPED, STATE_NULL = range(4)

    def __init__(self):
        self.__log = logging.getLogger('panucci.backends.BasePlayer')
        services.ObservableService.__init__(self, self.signals, self.__log)

        # Cached copies of position and duration
        self.__position, self.__duration = 0, 0
        self.seeking = False # Are we seeking?
        self.current_uri = None

    #############################################
    # Functions to be implemented by subclasses

    def get_position_duration(self):
        """ A cached version of _get_position_duration """
        if self.playing or self.paused:
            self.__position, self.__duration = self._get_position_duration()

        return self.__position, self.__duration

    def get_state(self):
        """ Get the current state of the player.

            Returns: One of the following flags: player.PLAYING,
                                                 player.PAUSED,
                                                 player.STOPPED,
                                                 or player.NULL
        """
        return self._get_state()

    def load_media(self, uri):
        """ Loads a uri into the player

            Params: uri - A full path to a media file.
                          Eg. file:///mnt/music/some-file.ogg
            Returns: Nothing
        """
        return self._load_media(uri)

    def pause(self):
        """ Pauses playback.

            Returns: The current position in nanoseconds.
            Signals: Must emit the "paused" signal.
        """
        return self._pause()

    def play(self, position=None):
        """ Starts playing the playlist's current track.

            Params: position is the absolute position to seek to before
                    playing. It is better to use this instead of relying on
                    play(); seek(...) because the player might not be ready to
                    seek at that point.
            Returns: False if the current track cannot be played.
                     True if all is well.
            Signals: Must emit the "playing" signal
        """
        return self._play()

    def stop(self, player=False):
        """ Stops playback.

            Params: player, if true delete player
            Returns: Nothing
            Signals: Must emit the "stopped" signal.
        """
        return self._stop(player)

    def seek(self, position):
        """ Seek to an absolute position in the current file.

            Params: position is the position to seek to in nanoseconds.
            Returns: True if the seek was successfull.
        """
        return self._seek(position)

    #############################################
    # Generic Functions

    def do_seek(self, from_beginning=None, from_current=None, percent=None):
        """ A very flexible function to seek in the current file

            Params: Requires ONE of the following keyword arguments
                    - from_beginning=n: seek n nanoseconds from the start of
                                        the file
                    - from_current=n: seek n nanoseconds from the current
                                      position
                    - percent=n: seek n percent from the beginning of the file

            Returns: False if the seek was NOT possible
                     ( position, duration ) if the seek was possible
        """
        error = False
        position, duration = self.get_position_duration()

        # if position and duration are 0 then player_get_position caught an
        # exception. Therefore self.__player isn't ready to be seeking.
        if not duration or self.get_state() == self.STATE_NULL:
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
            self.seek(position)
            return position, duration
        else:
            self.__log.debug('do_seek: Could not seek.')

        return False

    def play_pause_toggle(self):
        self.pause() if self.playing else self.play()

    @property
    def playing(self):
        """ Is the player playing? """
        return self.get_state() == self.STATE_PLAYING

    @property
    def paused(self):
        """ Is the player paused? """
        return self.get_state() == self.STATE_PAUSED

    @property
    def stopped(self):
        """ Is the player stopped? """
        return self.get_state() == self.STATE_STOPPED

    @property
    def null(self):
        """ Is the player stopped? """
        return self.get_state() == self.STATE_NULL

    def set_position_duration(self, pos, dur):
        """ used for setting pos and dur on startup"""
        self.__position, self.__duration = pos, dur

        return self.__position, self.__duration

    def reset_position_duration(self):
      self.__position, self.__duration = 0, 0
