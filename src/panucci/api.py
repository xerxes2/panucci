# -*- coding: utf-8 -*-

"""
Public API for Panucci

This module provides enough functionality to create a frontend to control
Panucci as well as exporting a large portion of the Panucci API over D-Bus.
"""

from __future__ import absolute_import

import dbus
import logging

from panucci import player
from panucci import services


class PanucciAPI(services.ForwardingObservableService, dbus.service.Object):
    """
    Panucci's public API for use in frontend development.
    
    
    Signal descriptions
    
    "playing"                       : ()
        Emitted when the file starts playing.
    "paused"                        : ()
        Emitted when the file is paused.
    "stopped"                       : ()
        Emitted when the file is stopped.
    "end-of-file"                   : ()
        Emitted when the player reaches the end of the file.
    "end-of-playlist"               : ()
        Emitted when the player reaches the end of the playlist.
    "new-track-loaded"              : ()
        Emitted when the player changes track.
    "new-metadata-available"        : ()
        Emitted when new metadata for the current track is available. Use
        the get_metadata function to retrieve it.
    "playlist-to-be-overwritten"    : ()
        Emitted when a playlist is about to be over-written. If the function
	    returns True the playlist will be over-written. Otherwise the
	    over-write will be aborted.
    "item-added"                    : ( item-id )
        Emitted when an item is added to the playlist.
    "item-removed"                  : ( item-id )
    "item-moved"                    : ( item-id, from-pos, to-pos )
    "bookmark-added"                : ( bookmark-id )
    "bookmark-removed"              : ( bookmark-id )
    """
    
    player_signals = {
        "new-metadata-available"    : "new-metadata-available",
        "playlist-to-be-overwritten": "playlist-to-be-overwritten",
        "end-of-playlist"           : "end-of-playlist",
        "item-removed"              : "item-removed",
        "item-moved"                : "item-moved",
        "bookmark-added"            : "bookmark-added",
        "new-track-loaded"          : "new-track-loaded",
        "bookmark-removed"          : "bookmark-removed",
        "item-added"                : "item-added", }
    
    playlist_signals = { "playing"      : "playing",
                         "paused"       : "paused",
                         "end-of-file"  : "eof",
                         "stopped"      : "stopped", }
    
    signals = player_signals.keys() + playlist_signals.keys()
    
    def __init__(self):
        self.__log = logging.getLogger("panucci.api.PanucciAPI")
        services.ForwardingObservableService.__init__( self,
                                                       self.signals,
                                                       self.__log )
        self.__player = player.player
        self.__playlist = self.__player.playlist
        
        self.forward( self.__player, self.player_signals )
        self.forward( self.__playlist, self.playlist_signals )
    
    def ready(self):
        """ Can be called by the frontend when it's initialized. This loads
            the last played track then sends the appropriate signals to
            populate the frontend's UI (namely: new-track-loaded and
            new-metadata-available) """
        
        self.__player.init()
    
    def quit(self):
        """ Should be called when the user exits the application. This stops
            the player and creates a resume bookmark. """
            
        self.__player.quit()
    
    
    def play(self):
        """ Starts playing the current track in the playlist. Does nothing if
            the playlist is empty or if the player is already playing. """
        
        return self.__player.play()
    
    def pause(self):
        """ Pauses the current track. Does nothing if the playlist is empty or
            the track is paused or stopped. """
        
        return self.__player.pause()
    
    def play_pause_toggle(self):
        """ Calls play() if the player is paused, calls pause() if the player
            is playing, does nothing if the player is stopped."""
        
        return self.__player.play_pause_toggle()
    
    def stop(self):
        """ Stop the currently playing (or paused) track. """
        
        return self.__player.stop()
    
    def next_track(self, loop=False):
        """ Changes to the next track in the playlist. If "loop" is set to
            True, then when the end of the playlist is reached it will loop
            to the beginning and continue playing. """
        
        return self.__playlist.skip( skip_by=1, loop=loop )
    
    def previous_track(self, loop=False):
        """ Changes to the previous track in the playlist. If "loop" is set to
            True and the current track is the first in the playlist then this
            function will skip to the last track in the playlist. """
        
        return self.__playlist.skip( skip_by=-1, loop=loop )
    
    def seek(self, from_beginning=None, from_current=None, percent=None ):
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
        
        return self.__player.do_seek( from_beginning = from_beginning,
                                      from_current = from_current,
                                      percent = percent )
    
    def get_position_duration(self):
        """ Returns the position in the current file and the duration in
            nanoseconds (10**-9). Returns ( -1, -1 ) if seeking is not possible
            or if no file is loaded. """
        
        return self.__player.get_position_duration()
    
    def get_metadata(self):
        """ Returns a dict containing metadata related to the current file
            being played. It can contain the following keys:
            "title"    - The title of the track
            "artist"   - The artist tag for the track
            "album"    - The album tag for the track
            "coverart" - A binary blob representing an image
            "length"   - The length in nanoseconds of the track
        """
        
        return self.__playlist.get_file_metadata()
    
    
    def play_uri(self, uri):
        """ Erase the playlist and start playing URI. The only supported URI
            at the moment is file:// followed by an absolute path.
            If the playlist has been modified since it was loaded a
            "playlist-to-be-overwritten" signal will be emitted. """
            
        return self.__playlist.load(uri)
    
    def play_directory(self, dirpath):
        """ Same as play_uri except dirpath is just an absolute path to a local
            directory. All the files in the directory will be loaded. """
        
        return self.__playlist.load_directory(dirpath)
    
    def queue_uri(self, uri):
        """ Adds a URI to the end of the playlist, see play_file for supported
            URIs. If the playlist is empty the file will start playing. """
        
        return self.__playlist.append(uri)
    
    def queue_directory(self, dirpath):
        """ Same as queue_uri except dirpath is just an absolute path to a local
            directory. All the files in the directory will be queued. """
        
        return self.__playlist.load_directory( dirpath, append=True )
    
    
    def add_bookmark_at_current_position( self, name=None ):
        """ Adds a bookmark at the current position in the track. The
            bookmark's name will be a formatted version of the position
            (hh:mm:ss). If a name is provided it will be used instead. """
        
        return self.__player.add_bookmark_at_current_position( label=name )
    
    
    def get_playlist_item_data( self, item_id ):
        """ """
        
    def remove_bookmark(self, bookmark_id):
        """ """
    
    
    def get_recent_files(self):
        """ """
    
    
    def show_main_window(self):
        """ """
    
