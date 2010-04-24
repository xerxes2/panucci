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

import logging

import panucci
from panucci.settings import settings
from panucci.services import ObservableService


class BASE_ERROR:
    pass
class BASE_ERROR_NO_MEDIA(BASE_ERROR):
    error = _("No media selected")
class BASE_ERROR_UNSUPPORTED(BASE_ERROR):
    error = _("Unsupported filetype.")
class BASE_ERROR_BACKEND(BASE_ERROR):
    error = _("Something wrong with the backend")
class BASE_ERROR_HARDWARE(BASE_ERROR):
    error = _("Hardware blocked/in-use")
class BASE_ERROR_BAD_FILE(BASE_ERROR):
    error = _("File is corrupted/incomplete")
class BASE_ERROR_FILE_NOT_FOUND(BASE_ERROR):
    error = _("File not found, make sure the file still exists.")


class BasePlayer(ObservableService):
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
        ObservableService.__init__(self, self.signals, self.__log)
        settings.register( 'volume_changed', self._set_volume_level )
        
        # Cached copies of position and duration
        self.__position, self.__duration = 0, 0
        self.seeking = False # Are we seeking?
    
    
    #############################################
    # Functions to be implemented by subclasses
    
    def get_state(self):
        """ Get the current state of the player.
            
            Returns: One of the following flags: player.PLAYING,
                                                 player.PAUSED,
                                                 player.STOPPED,
                                                 or player.NULL
        """
    
    def load_media(self, uri):
        """ Loads a uri into the player
            
            Params: uri - A full path to a media file.
                          Eg. file:///mnt/music/some-file.ogg
            Returns: Nothing
        """
    
    def pause(self):
        """ Pauses playback.
            
            Returns: The current position in nanoseconds.
            Signals: Must emit the "paused" signal.
        """
    
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
    
    def stop(self):
        """ Stops playback.
        
            Returns: Nothing
            Signals: Must emit the "stopped" signal.
        """
    
    def _get_position_duration(self):
        """ Get the position and duration of the current file.
            
            Returns: ( current position, total duration )
        """
    
    def _seek(self, position):
        """ Seek to an absolute position in the current file.
            
            Params: position is the position to seek to in nanoseconds.
            Returns: True if the seek was successfull.
        """
    
    def _set_volume_level(self, level):
        """ Sets the volume level of the player. This should only be used in
            conjunction with the settings manager's "volume_changed" signal.
            
            Params: level is a float between 0 and 1.
            Returns: Nothing
        """
    
    
    #############################################
    # Generic Functions
    
    def do_seek(self, from_beginning=None, from_current=None, percent=None ):
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
        if not duration or self.get_state == self.STATE_NULL:
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
            self._seek(position)
            return position, duration
        else:
            self.__log.debug('do_seek: Could not seek.')

        return False
    
    def get_position_duration(self):
        """ A cached version of _get_position_duration """
        if self.playing:
            self.__position, self.__duration = self._get_position_duration()
        
        return self.__position, self.__duration
    
    def play_pause_toggle(self):
        self.pause() if self.playing else self.play()
    
    @property
    def playing(self):
        """ Is the player playing? """
        return self.get_state() == self.STATE_PLAYING
    
