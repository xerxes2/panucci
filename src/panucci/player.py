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

from playlist import Playlist
from settings import settings
from services import ObservableService
from dbusinterface import interface
from backends import osso, gstplaybin

import util


class PanucciPlayer(ObservableService):
    """
    A proxy object which adds a layer of abstraction between all the different
    backends. It picks the right backend for the job and forwards signals from
    them.
    """
    signals = [ "playing", "paused", "stopped", "eof" ]
    
    def __init__(self, player):
        self.__log = logging.getLogger('panucci.player.PanucciPlayer')
        ObservableService.__init__(self, self.signals, self.__log)
        self.__player = player
        
        # Forward the following signals (messy...)
        self.__player.register( "playing", lambda: self.notify("playing"))
        self.__player.register( "playing", self.on_playing)
        self.__player.register( "paused",  lambda *x: self.notify("paused", *x))
        self.__player.register( "stopped", lambda: self.notify("stopped"))
        self.__player.register( "eof",     lambda: self.notify("eof"))
        
        self.playlist = Playlist()
        self.playlist.register( 'new-track-loaded', self.on_new_track )
        self.playlist.register( 'seek-requested', self.do_seek )
        self.playlist.register( 'stop-requested', self.stop )
        settings.register( 'volume_changed', self._set_volume_level )
        
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
    
    def add_bookmark_at_current_position( self ):
        """ Adds a bookmark at the current position
            
            Returns: (bookmark lable string, position in nanoseconds)
        """
        
        label, position = player.get_formatted_position()
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
    
    def on_new_track(self):
        """ New track callback; stops the player and starts the new track. """
        
        self.stop()
        self.load_media( "file://" + self.playlist.current_filepath )
        
        # This is just here to prevent the player from starting to play
        # when it is first opened. The first time this function is called it
        # doesn't run self.play(), but otherwise it will.
        if hasattr( self, "__initialized" ):
            self.play()
        else:
            self.__initialized = True
    
    def on_playing(self):
        """ 
        Used to seek to the correct position once the file has started
        playing. This has to be done once the player is ready because
        certain player backends can't seek in any state except playing.
        """
        
        seek = self.playlist.play()
        if seek > 0:
            self._seek(seek)
    
    def quit(self):
        """ Called when the application exits """
        self.playlist.stop( self.get_position_duration()[0] )
        self.stop()
        self.playlist.quit()
    

if util.platform == util.MAEMO:
    backend = osso.ossoPlayer
else:
    backend = gstplaybin.GstPlaybinPlayer

# there should only ever be one panucciPlayer object
player = PanucciPlayer( backend() )

