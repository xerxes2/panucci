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

import time
import os
import logging
import random

import panucci
from panucci.dbsqlite import db
from panucci.services import ObservableService
from panucci.dbusinterface import interface
from panucci import playlistformat
from panucci import player
from panucci import util

def is_supported(uri):
    filename, extension = os.path.splitext(uri)
    if extension.startswith('.'):
        extension = extension[1:]

    return (extension.lower() in panucci.EXTENSIONS)

class Playlist(ObservableService):
    signals = [ 'new-track-loaded', 'new-metadata-available', 'file_queued',
                'bookmark_added', 'seek-requested', 'end-of-playlist',
                'playlist-to-be-overwritten', 'stop-requested', 'reset-playlist',
                'stopped', 'playing', 'paused' ]

    def __init__(self, config):
        self.__log = logging.getLogger('panucci.playlist.Playlist')
        ObservableService.__init__(self, self.signals, self.__log)
        self.config = config
        self.filepath = panucci.PLAYLIST_FILE
        self._id = None

        self.__player = player.PanucciPlayer(self.config)
        self.__player.register('eof', self.on_player_eof)
        self.__player.register('playing', self.on_player_playing)
        self.__player.register('paused', self.on_player_paused)
        self.__player.register('stopped', self.on_player_stopped)
        self.__queue = Queue(self.id)
        self.__queue.register('current_item_changed', self.on_queue_current_item_changed)

        # Register the d-bus interface only once we're ready
        interface.register_playlist(self)

    def init(self, filepath=None):
        """ Start playing the current file in the playlist or a custom file.
            This should be called by the UI once it has initialized.

            Params: filepath is an optional filepath to the first file that
                    should be loaded/played
            Returns: Nothing
        """

        if filepath is None or not self.load( filepath ):
            self.load_last_played()
            position = self.get_seek_to()
            self.set_position_duration(position, 0)
            self.do_seek(position)
        else:
            self.play()

    def reset_playlist(self):
        """ Sets the playlist to a default "known" state """

        #self.notify('stop-requested', caller=self.reset_playlist)
        self.stop()
        self.filepath = None
        self._id = None
        self.__queue.clear()
        self.reset_player()
        self.notify('reset-playlist', caller=self.reset_playlist)

    @property
    def id(self):
        if self.filepath is None:
            self.__log.warning("Can't get playlist id without having filepath")
        elif self._id is None:
                self._id = db.get_playlist_id( self.filepath, True, True )

        return self._id

    @property
    def current_filepath(self):
        """ Get the current file """
        if not self.is_empty:
            return self.__queue.current_item.filepath

    @property
    def queue_modified(self):
        return self.__queue.modified

    @property
    def queue_length(self):
        return len(self.__queue)

    @property
    def is_empty(self):
        return not self.__queue

    def print_queue_layout(self):
        """ This helps with debugging ;) """
        for item in self.__queue:
            print str(item), item.playlist_reported_filepath
            for bookmark in item.bookmarks:
                print '\t', str(bookmark), bookmark.bookmark_filepath

    def save_to_new_playlist(self, filepath, playlist_type='m3u'):
        self.filepath = filepath
        self._id = None

        playlist = { 'm3u': playlistformat.M3U_Playlist, 'pls': playlistformat.PLS_Playlist }
        if not playlist.has_key(playlist_type):
            playlist_type = 'm3u' # use m3u by default
            self.filepath += '.m3u'

        playlist = playlist[playlist_type](self.filepath, self.__queue)
        if not playlist.export_items( filepath ):
            self.__log.error('Error exporting playlist to %s', self.filepath)
            return False

        # copy the bookmarks over to new playlist
        db.remove_all_bookmarks(self.id)
        self.__queue.set_new_playlist_id(self.id)

        return True

    def save_temp_playlist(self):
        return self.save_to_new_playlist(panucci.PLAYLIST_FILE)

    def on_queue_current_item_changed(self):
        self.new_track_loaded()

    def send_metadata(self):
        self.notify( 'new-metadata-available', caller=self.send_metadata )

    def start_of_playlist(self):
        """Checks if the currently played item is the first"""
        if self.__queue.current_item_position == 0:
            return True

    def end_of_playlist(self):
        """Checks if the currently played item is the last"""
        if len(self.__queue.get_items()) - 1 == self.__queue.current_item_position:
            return True

    def get_formatted_position(self, pos=None):
        """ Gets the current position and converts it to a human-readable str.

            Returns: (bookmark lable string, position in nanoseconds)
        """

        if pos is None:
            (pos, dur) = self.get_position_duration()

        text = util.convert_ns(pos)
        return (text, pos)

    def get_current_item(self):
        return self.__queue.current_item

    def quit(self):
        self.__log.debug('quit() called.')
        #self.notify('stop-requested', caller=self.quit)
        self.stop()
        if self.__queue.modified:
            self.__log.info('Queue modified, saving temporary playlist')
            self.save_temp_playlist()

    ######################################
    # Bookmark-related functions
    ######################################

    def __load_from_bookmark(self, item_id, bookmark):
        new_pos = self.__queue.index(item_id)
        same_pos = self.__queue.current_item_position == new_pos
        if not same_pos:
            self.__queue.current_item_position = new_pos

        if bookmark is None:
            seek_position = 0
        else:
            seek_position = bookmark.seek_position
            self.__queue.current_item.seek_to = seek_position

        if same_pos:
            if self.playing or seek_position == 0:
                self.do_seek(seek_position)
        if not self.playing:
            self.play()

        return True

    def load_from_bookmark_id(self, item_id=None, bookmark_id=None, set_seek_to=True):
        item, bookmark = self.__queue.get_bookmark(item_id, bookmark_id)
        if str(self.__queue.current_item) != item_id and not self.null:
            #self.notify('stop-requested', caller=self.load_from_bookmark_id)
            self.stop(False, set_seek_to)

        if item is not None:
            return self.__load_from_bookmark( str(item), bookmark )
        else:
            self.__log.warning(
                'item_id=%s,bookmark_id=%s not found', item_id, bookmark_id )
            return False

    def find_resume_bookmark(self):
        """ Find a resume bookmark in the queue """
        for item in self.__queue:
            for bookmark in item.bookmarks:
                if bookmark.is_resume_position:
                    return str(item), str(bookmark)
        else:
            return None, None

    def load_from_resume_bookmark(self):
        item_id, bookmark_id = self.find_resume_bookmark()
        if None in ( item_id, bookmark_id ):
            self.__log.info('No resume bookmark found.')
            return False
        else:
            return self.load_from_bookmark_id(item_id, bookmark_id, False)

    def save_bookmark( self, bookmark_name, position ):
        if self.__queue.current_item is not None:
            self.__queue.current_item.save_bookmark( bookmark_name, position,
                                                     resume_pos=False )
            self.notify( 'bookmark_added', str(self.__queue.current_item),
                         bookmark_name, position, caller=self.save_bookmark )

    def update_bookmark(self, item_id, bookmark_id, name=None, seek_pos=None):
        item, bookmark = self.__queue.get_bookmark(item_id, bookmark_id)

        if item is None:
            self.__log.warning('No such item id (%s)', item_id)
            return False

        if bookmark_id is not None and bookmark is None:
            self.__log.warning('No such bookmark id (%s)', bookmark_id)
            return False

        if bookmark_id is None:
            if name and item.title != name:
                item.title = name
                self.__queue.modified = True
            if self.__queue.current_item == item:
                self.notify( 'new-metadata-available',
                             caller=self.update_bookmark )
        else:
            bookmark.timestamp = time.time()

            if name is not None:
                bookmark.bookmark_name = name

            if seek_pos is not None:
                bookmark.seek_position = seek_pos

            db.update_bookmark(bookmark)

        return True

    def update_bookmarks(self):
        """ Updates the database entries for items that have been modified """
        for item in self.__queue:
            if item.is_modified:
                self.__log.debug('Playlist Item "%s" is modified, updating bookmarks', item)
                item.update_bookmarks()
                item.is_modified = False

    def remove_bookmark( self, item_id, bookmark_id ):
        item = self.__queue.get_item(item_id)

        if item is None:
            self.__log.info('Cannot find item with id: %s', item_id)
            return False

        if not bookmark_id:
            if self.__queue.current_item_position == self.__queue.index(item):
                is_end = self.end_of_playlist()
                self.stop()
                item.delete_bookmark(None)
                self.__queue.remove(item)
                if not is_end:
                    self.__queue.current_item_position = self.__queue.current_item_position
                elif not self.is_empty:
                    self.__queue.current_item_position = 0
                else:
                    self.reset_playlist()
            else:
                item.delete_bookmark(None)
                self.__queue.remove(item)
        else:
            item.delete_bookmark(bookmark_id)

        return True

    def delete_all_bookmarks(self):
        db.delete_all_bookmarks()
        for item in self.__queue.get_items():
            item.delete_bookmark(None)

    def remove_resume_bookmarks(self):
        item_id, bookmark_id = self.find_resume_bookmark()

        if None in ( item_id, bookmark_id ):
            return False
        else:
            return self.remove_bookmark( item_id, bookmark_id )

    def add_bookmark_at_current_position( self, label=None ):
        """ Adds a bookmark at the current position
            Returns: (bookmark lable string, position in nanoseconds)
        """

        default_label, position = self.get_formatted_position()
        label = default_label if label is None else label
        self.save_bookmark( label, position )
        self.__log.info('Added bookmark: %s - %d', label, position)
        return label, position

    def move_item( self, from_row, to_row ):
        self.__log.info('Moving item from position %d to %d', from_row, to_row)
        assert isinstance(from_row, int) and isinstance(to_row, int)
        self.__queue.move_item(from_row, to_row)

    #####################################
    # Model-builder functions
    #####################################

    def get_item_by_id(self, item_id):
        """ Gets a PlaylistItem from it's unique id """

        item, bookmark = self.__queue.get_bookmark(item_id, None)
        if item is None:
            self.__log.warning('Cannot get item for id: %s', item_id)

        return item

    def get_playlist_item_ids(self):
        """ Returns an iterator which yields a tuple which contains the
            item's unique ID and a dict of interesting data (currently
            just the title). """
        
        for item in self.__queue:
            yield str(item), { 'title' : item.title }

    def get_bookmarks_from_item_id(self, item_id, include_resume_marks=False):
        """ Returns an iterator which yields the following data regarding a
            bookmark: ( bookmark id, a custom name, the seek position ) """

        item = self.get_item_by_id( item_id )
        if item is not None:
            for bkmk in item.bookmarks:
                if not bkmk.is_resume_position or include_resume_marks:
                    yield str(bkmk), bkmk.bookmark_name, bkmk.seek_position

    ######################################
    # File-related convenience functions
    ######################################

    def get_current_position(self):
        """ Returns the saved position for the current
                file or 0 if no file is available"""
        if not self.is_empty:
            return self.__queue.current_item.seek_to
        else:
            return 0

    def get_current_filetype(self):
        """ Returns the filetype of the current
                file or None if no file is available """

        if not self.is_empty:
            return self.__queue.current_item.filetype

    def get_file_metadata(self):
        """ Return the metadata associated with the current FileObject """
        if not self.is_empty:
            return self.__queue.current_item.metadata
        else:
            return {}

    def get_current_filepath(self):
        if not self.is_empty:
            return self.__queue.current_item.filepath

    def get_recent_files(self, max_files=10):
        files = db.get_latest_files()

        if len(files) > max_files:
            return files[:max_files]
        else:
            return files

    ##################################
    # File importing functions
    ##################################

    def load(self, filepath, play=True):
        """ Detects filepath's filetype then loads it using
            the appropriate loader function """
        self.__log.debug('Attempting to load %s', filepath)
        _play = self.is_empty or (self.end_of_playlist() and not self.get_position_duration()[0])
        if self.is_empty:
            _position = 0
        else:
            _position = len(self.__queue)
        error = False

        if os.path.isdir(filepath):
            self.load_directory(filepath, True)
        else:
            parsers = {'m3u': playlistformat.M3U_Playlist, 'pls': playlistformat.PLS_Playlist}
            extension = util.detect_filetype(filepath)
            if parsers.has_key(extension): # importing a playlist
                self.__log.info('Loading playlist file (%s)', extension)
                parser = parsers[extension](filepath, self.__queue)
                self.filepath = filepath
                self._id = None
                self.__queue.playlist_id = self.id
                if parser.parse(filepath):
                    self.__queue = parser.get_queue()
                    self.__file_queued( filepath, True, False )
                else:
                   return False
            else:                          # importing a single file
                error = not self.append(filepath, notify=False)

        # if we let the queue emit a current_item_changed signal (which will
        # happen if load_from_bookmark changes the current track), the player
        # will start playing and ingore the resume point
        self.__queue.modified = True
        if _play and not self.is_empty:
            if not self.null:
                self.stop(False, False)
            if _position == 0:
                self.__queue.disable_notifications = True
                self.load_from_resume_bookmark()
                self.__queue.disable_notifications = False
            else:
                self.__queue.set_current_item_position(_position)
            #self.notify( 'stop-requested', caller=self.load )
            self.new_track_loaded()
            if play:
                self.play()
            #self.notify( 'new-track-loaded', caller=self.load )
            #self.notify( 'new-metadata-available', caller=self.load )

        return not error

    def load_last_played(self):
        recent = self.get_recent_files(max_files=1)
        if recent:
            self.load(recent[0], False)
        return bool(recent)

    def __file_queued(self, filepath, successfull, notify):
        if successfull:
            self.notify( 'file_queued', filepath, successfull, notify,
                caller=self.__file_queued )

        return successfull

    def append(self, filepath, notify=True):
        self.__log.debug('Attempting to queue file: %s', filepath)
        success = self.__queue.append(
            playlistformat.PlaylistItem.create_by_filepath(filepath, filepath) )
        return self.__file_queued( filepath, success, notify)

    def insert(self, position, filepath ):
        self.__log.debug(
            'Attempting to insert %s at position %s', filepath, position )
        return self.__file_queued( filepath, self.__queue.insert( position,
            playlistformat.PlaylistItem.create_by_filepath(filepath, filepath)), True )

    def load_directory(self, directory, append=False):
        self.__log.debug('Attempting to load directory "%s"', directory)

        if not os.path.isdir(directory):
            self.__log.warning('"%s" is not a directory.', directory)
            return False

        if not append:
            if self.notify( 'playlist-to-be-overwritten',
                            caller=self.load_directory ):
                self.reset_playlist()
            else:
                self.__log.info('Directory load aborted by user.')
                return False

        self.filepath = panucci.PLAYLIST_FILE
        self.__queue.playlist_id = self.id

        items = []
        potential_items = os.listdir(directory)
        potential_items.sort()

        for item in potential_items:
            filepath = os.path.join( directory, item )
            if os.path.isfile(filepath) and is_supported(filepath):
                items.append(filepath)

        items.sort()
        for item in items:
            self.append( item, notify=False )

        if not append:
            self.on_queue_current_item_changed()

        return True

    ##################################
    # Playlist controls
    ##################################

    def set_seek_to(self, seek_to, seconds=False):
        """Set the seek-to position for the current track"""
        if seconds:
            seek_to = (10**9) * seek_to
        if not self.is_empty:
            self.get_current_item().seek_to = seek_to

    def set_seek_to_from_current(self):
        self.set_seek_to(self.get_position_duration()[0])

    def reset_all_seek_to(self):
        self.set_seek_to(self.get_position_duration()[0])
        for item in self.__queue.get_items():
            item.seek_to = 0

    def get_seek_to(self, reset=True):
        """Get the seek-to position for the current track"""
        if not self.is_empty:
            seek_to = self.__queue.current_item.seek_to
            if reset:
                self.get_current_item().seek_to = 0
        else:
            seek_to = 0
        return seek_to

    def skip(self, loop=True, skip_by=None, skip_to=None, set_seek_to=True, play=True):
        """ Skip to another track in the playlist.
            Use either skip_by or skip_to, skip_by has precedence.
                skip_to: skip to a known playlist position
                skip_by: skip by n number of episodes (positive or negative)
                loop: loop if the track requested lays out of
                      the 0 to queue_length-1 boundary.
        """
        if not self.__queue:
            return False

        current_item_position = self.__queue.current_item_position

        if skip_by is not None:
            skip = current_item_position + skip_by
        elif skip_to is not None:
            skip = skip_to
        else:
            skip = 0
            self.__log.warning('No skip method provided...')

        if not 0 <= skip < self.queue_length:
            #self.notify( 'end-of-playlist', loop, caller=self.skip )

            if not loop:
                self.__log.warning( "Can't skip to non-existant file w/o loop."
                                    " (requested=%d, total=%d)", skip,
                                    self.queue_length )
                return False
            else:
                # If skip_by is given as an argument, we assume the user knows
                # what they're doing. Ie. if the queue length is 5, current
                # track is 3 and they pass skip_by=-9, then they'll end up
                # at 4. On the other hand, if skip_to is passed then we skip
                # back to 0 because in that case the user must enter a number
                # from 0 to queue_length-1, anything else is an error.
                if skip_by is not None:
                    skip %= self.queue_length
                else:
                    skip = 0

        #self.notify('stop-requested', caller=self.skip)
        self.stop(False, set_seek_to)
        self.__queue.current_item_position = skip
        self.__log.debug('Skipping to file %d (%s)', skip, self.__queue.current_item.filepath)
        if play:
            self.play()

        return True

    def next(self, loop=False, set_seek_to=True):
        """ Move the playlist to the next track.
            False indicates end of playlist. """
        return self.skip(loop, 1, None, set_seek_to)

    def prev(self, set_seek_to=True):
        """ Same as next() except moves to the previous track. """
        return self.skip(False, -1, None, set_seek_to)

    def last(self, set_seek_to=True, play=True):
        """ Plays last file in queue. """
        skip_to = len(self.__queue.get_items()) - 1
        return self.skip(False, None, skip_to, set_seek_to, play)

    def random(self, set_seek_to=True):
        """ Plays random file in queue. """
        skip_to = random.choice(range(len(self.__queue.get_items())))
        return self.skip(False, None, skip_to, set_seek_to)

    ##################################
    # Player controls
    ##################################

    def play(self):
        """ This gets called by the player to get
                the last time the file was paused """
        self.__player.play()

    def pause(self):
        """ Called whenever the player is paused """
        #position = self.get_position_duration()[0]
        #self.__queue.current_item.seek_to = position
        self.__player.pause()

    def play_pause_toggle(self):
        if self.current_filepath:
            self.__player.play_pause_toggle()

    def stop(self, save_resume_point=True, set_seek_to=True):
        """ This should be run when the program is closed
                or if the user switches playlists """
        position, duration = self.get_position_duration()
        self.remove_resume_bookmarks()
        self.on_player_stopped()
        self.__player.on_stop_requested()
        if not self.is_empty and save_resume_point:
            self.get_current_item().save_bookmark(_('Auto Bookmark'), position, True)
        if not self.is_empty and set_seek_to and self.config.getboolean("options", "resume_all"):
            self.set_seek_to(position)

    def on_player_eof(self):
        play_mode = self.config.get("options", "play_mode")
        if play_mode == "single":
            if not self.config.getboolean("options", "stay_at_end"):
                self.stop(set_seek_to=False)
                self.notify('end-of-playlist', False, caller=self.on_player_eof)
        elif play_mode == "random":
            self.random(set_seek_to=False)
        elif play_mode == "repeat":
            self.next(loop=True, set_seek_to=False)
        else:
            if self.end_of_playlist():
                if not self.config.getboolean("options", "stay_at_end"):
                   self.stop(set_seek_to=False)
            else:
                self.next(loop=False, set_seek_to=False)

    def on_player_playing(self):
        self.__player.on_playing(self.get_seek_to())
        self.notify("playing", caller=self.on_player_playing)

    def on_player_paused(self, position, duration):
        self.notify("paused", position, duration, caller=self.on_player_paused)

    def on_player_stopped(self):
        self.notify("stopped", caller=self.on_player_stopped)

    def do_seek(self, from_beginning=None, from_current=None,  percent=None):
        resp = None
        if from_beginning is not None:
            resp = self.__player.do_seek(from_beginning=from_beginning)
        elif from_current is not None:
            if not self.config.getboolean("options", "seek_back") or self.start_of_playlist() or from_current > 0:
                resp = self.__player.do_seek(from_current=from_current)
            else:
                pos_int, dur_int = self.get_position_duration()
                if pos_int + from_current >= 0:
                    resp = self.__player.do_seek(from_current=from_current)
                else:
                    self.prev()
                    pos_int, dur_int = self.get_position_duration()
                    resp = self.__player.do_seek(from_beginning=dur_int+from_current)
        elif percent is not None:
            resp = self.__player.do_seek(percent=percent)
        return resp

    def get_position_duration(self):
        return self.__player.get_position_duration()

    def set_position_duration(self, position, duration):
        self.__player.set_position_duration(position, duration)

    @property
    def playing(self):
        return self.__player.playing

    @property
    def paused(self):
        return self.__player.paused

    @property
    def stopped(self):
        return self.__player.stopped

    @property
    def null(self):
        return self.__player.null

    @property
    def seeking(self):
        return self.__player.seeking

    def new_track_loaded(self):
        if os.path.isfile(self.current_filepath):
            self.__player.load_media(self.current_filepath)
            self.notify('new-track-loaded', caller=self.new_track_loaded)
            self.notify('new-metadata-available', caller=self.new_track_loaded)
        elif not self.end_of_playlist():
            self.on_player_eof()

    def reset_player(self):
        self.__player.on_reset_playlist()

    def get_volume_level(self):
        return self.__player.get_volume_level()

    def set_volume_level(self, percent):
        self.__player.set_volume_level(percent)

class Queue(list, ObservableService):
    """ A Simple list of PlaylistItems """

    signals = [ 'current_item_changed', ]

    def __init__(self, playlist_id):
        self.__log = logging.getLogger('panucci.playlist.Queue')
        ObservableService.__init__(self, self.signals, self.__log)

        self.playlist_id = playlist_id
        self.modified = False # Has the queue been modified?
        self.disable_notifications = False
        self.__current_item_position = 0
        # This is a hack and WILL BE REPLACED WITH SOMETHING BETTER.
        # it's here to speed up the get_item function
        self.__mapping_dict = {}
        list.__init__(self)

    def __get_current_item_position(self):
        return self.__current_item_position

    def __set__current_item_position(self, new_value):

        # set the new position before notify()'ing
        # or else we'll end up load the old file's metadata
        old_value = self.__current_item_position
        self.__current_item_position = new_value

        if old_value != new_value:
            self.__log.debug( 'Current item changed from %d to %d',
                old_value, new_value )
            if not self.disable_notifications:
                self.notify( 'current_item_changed',
                    caller=self.__set__current_item_position )
        else:
            self.__log.debug( 'Current item reloaded')
            if not self.disable_notifications:
                self.notify( 'current_item_changed',
                    caller=self.__set__current_item_position )

    current_item_position = property(
        __get_current_item_position, __set__current_item_position )

    def __count_dupe_items(self, subset, item):
        # Count the number of duplicate items (by filepath only) in a list
        tally = 0
        for i in subset:
            tally += int( i.filepath == item.filepath )
        return tally

    def __prep_item(self, item):
        """ Do some error checking and other stuff that's
            common to the insert and append functions """

        assert isinstance( item, playlistformat.PlaylistItem )
        item.playlist_id = self.playlist_id

        if '://' in item.filepath or (os.path.isfile(item.filepath) and \
                is_supported(item.filepath)):
            self.modified = True
            return True
        else:
            self.__log.warning(
                'File not found or not supported: %s', item.filepath )

            return False

    @property
    def current_item(self):
        if len(self) > 0:
            if self.current_item_position >= len(self):
                self.__log.info( 'Current item position is greater '
                    'than queue length, resetting to 0.' )
                self.current_item_position = 0

            return self[self.current_item_position]
        else:
            self.__log.info('Queue is empty...')

    def move_item(self, from_pos, to_pos):
        old_current_item = self.current_item_position

        temp = self[from_pos]
        self.remove(str(temp))
        self.insert(to_pos, temp)

        if old_current_item == from_pos:
            self.__current_item_position = to_pos

    def clear(self):
        """ Reset the the queue to a known state """

        try:
            items = self.__mapping_dict.values()
            for item in items:
              list.remove(self, item)
        except:
          pass
        self[:] = []
        self.playlist_id = None
        self.modified = True
        self.__current_item_position = 0
        self.__mapping_dict = {}

    def get_item(self, item_id):
        return self.__mapping_dict.get(item_id)

    def get_items(self):
        return self.__mapping_dict.values()

    def is_empty(self):
        if self.__mapping_dict:
            return False
        else:
            return True

    def get_bookmark(self, item_id, bookmark_id):
        item = self.get_item(item_id)

        if item is None:
            self.__log.warning(
                'Item with id "%s" not found, scanning for item...', item_id )

            for item_ in self:
                if item_.bookmarks.count(bookmark_id):
                    item = item_
                    break

            if item is None: return None, None

        if item.get_bookmark(bookmark_id):
            return item, item.get_bookmark(bookmark_id)
        else:
            return item, None

    def set_new_playlist_id(self, id):
        self.playlist_id = id
        for item in self:
            item.playlist_id = id
            for bookmark in item.bookmarks:
                bookmark.playlist_id = id
                bookmark.save()

    def insert(self, position, item):
        if not self.__prep_item(item):
            return False

        item.duplicate_id = self[:position].count(item)

        if self.__count_dupe_items(self[position:], item):
            for i in self[position:]:
                if i.filepath == item.filepath:
                    i.is_modified = True
                    i.duplicate_id += 1

            # to be safe rebuild self.__mapping_dict
            self.__mapping_dict = dict([(str(i),i) for i in self])
        elif not self.__count_dupe_items(self[:position], item):
            # there are no other items like this one so it's *safe* to load
            # bookmarks without a potential conflict, but there's a good chance
            # that there aren't any bookmarks to load (might be useful in the
            # event of a crash)...
            item.load_bookmarks()

        if position <= self.current_item_position:
            self.__current_item_position += 1

        self.__mapping_dict[str(item)] = item
        list.insert(self, position, item)
        return True

    def append(self, item):
        if not self.__prep_item(item):
            return False

        item.playlist_id = self.playlist_id
        item.duplicate_id = self.__count_dupe_items(self, item)
        item.load_bookmarks()

        self.__mapping_dict[str(item)] = item
        list.append(self, item)
        return True

    def remove(self, item):
        if self.count(item):
            self.modified = True

            if self.index(item) < self.current_item_position:
                self.__current_item_position -= 1

            del self.__mapping_dict[str(item)]
            list.remove(self, item)

    def extend(self, items):
        self.__log.warning('FIXME: extend not supported yet...')

    def pop(self, item):
        self.__log.warning('FIXME: pop not supported yet...')

    def set_current_item_position(self, position):
        self.__current_item_position = position
