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

import gobject, gtk
import time
import os.path
import os
import re
import logging
from hashlib import md5
from xml.sax.saxutils import escape

import panucci

from panucci.dbsqlite import db
from panucci.services import ObservableService

from panucci import util

def is_supported(uri):
    filename, extension = os.path.splitext(uri)
    if extension.startswith('.'):
        extension = extension[1:]

    return (extension.lower() in panucci.EXTENSIONS)

class Playlist(ObservableService):
    signals = [ 'new-track-loaded', 'new-metadata-available', 'file_queued',
                'bookmark_added', 'seek-requested', 'end-of-playlist',
                'playlist-to-be-overwritten', 'stop-requested' ]

    def __init__(self):
        self.__log = logging.getLogger('panucci.playlist.Playlist')
        ObservableService.__init__(self, self.signals, self.__log)

        self.__queue = Queue(None)
        self.__queue.register(
            'current_item_changed', self.on_queue_current_item_changed )

        self.reset_playlist()

    def reset_playlist(self):
        """ Sets the playlist to a default "known" state """

        self.filepath = None
        self._id = None
        self.__queue.clear()

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

        playlist = { 'm3u': M3U_Playlist, 'pls': PLS_Playlist }
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
        self.notify( 'new-track-loaded',
                     caller=self.on_queue_current_item_changed )
        self.notify( 'new-metadata-available',
                     caller=self.on_queue_current_item_changed )

    def send_metadata(self):
        self.notify( 'new-metadata-available', caller=self.send_metadata )

    def quit(self):
        self.__log.debug('quit() called.')
        if self.__queue.modified:
            self.__log.info('Queue modified, saving temporary playlist')
            self.save_temp_playlist()

    ######################################
    # Bookmark-related functions
    ######################################

    def __load_from_bookmark( self, item_id, bookmark ):
        new_pos = self.__queue.index(item_id)
        same_pos = self.__queue.current_item_position == new_pos
        self.__queue.current_item_position = new_pos

        if bookmark is None:
            self.__queue.current_item.seek_to = 0
        else:
            self.__queue.current_item.seek_to = bookmark.seek_position

            # if we don't request a seek nothing will happen
            if same_pos:
                self.notify( 'seek-requested', bookmark.seek_position,
                    caller=self.__load_from_bookmark )

        return True

    def load_from_bookmark_id( self, item_id=None, bookmark_id=None ):
        item, bookmark = self.__queue.get_bookmark(item_id, bookmark_id)
        if self.__queue.current_item != item_id:
            self.notify('stop-requested', caller=self.load_from_bookmark_id)

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
            return self.load_from_bookmark_id( item_id, bookmark_id )

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
                self.__log.debug(
                    'Playlist Item "%s" is modified, updating bookmarks', item)
                item.update_bookmarks()
                item.is_modified = False

    def remove_bookmark( self, item_id, bookmark_id ):
        item = self.__queue.get_item(item_id)

        if item is None:
            self.__log.info('Cannot find item with id: %s', item_id)
            return False

        if bookmark_id is None:
            if self.__queue.current_item_position == self.__queue.index(item_id):
                self.next()

            item.delete_bookmark(None)
            self.__queue.remove(item_id)
        else:
            item.delete_bookmark(bookmark_id)

        return True

    def remove_resume_bookmarks(self):
        item_id, bookmark_id = self.find_resume_bookmark()

        if None in ( item_id, bookmark_id ):
            return False
        else:
            return self.remove_bookmark( item_id, bookmark_id )

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

    def load(self, filepath):
        """ Detects filepath's filetype then loads it using
            the appropriate loader function """
        self.__log.debug('Attempting to load %s', filepath)

        if ( self.queue_modified and
            not self.notify( 'playlist-to-be-overwritten', caller=self.load )):

            self.__log.info('Loading file aborted by user.')
            return False

        self.notify( 'stop-requested', caller=self.load )

        error = False
        self.reset_playlist()
        self.filepath = filepath
        self.__queue.playlist_id = self.id

        parsers = { 'm3u': M3U_Playlist, 'pls': PLS_Playlist }
        extension = util.detect_filetype(filepath)
        if parsers.has_key(extension): # importing a playlist
            self.__log.info('Loading playlist file (%s)', extension)
            parser = parsers[extension](self.filepath, self.__queue)

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
        self.__queue.disable_notifications = True
        self.load_from_resume_bookmark()
        self.__queue.disable_notifications = False

        self.__queue.modified = (self.filepath == panucci.PLAYLIST_FILE)

        self.notify( 'new-track-loaded', caller=self.load )
        self.notify( 'new-metadata-available', caller=self.load )

        return not error

    def load_last_played(self):
        recent = self.get_recent_files(max_files=1)
        if recent:
            self.load(recent[0])

        return bool(recent)

    def __file_queued(self, filepath, successfull, notify):
        if successfull:
            self.notify( 'file_queued', filepath, successfull, notify,
                caller=self.__file_queued )

        return successfull

    def append(self, filepath, notify=True):
        self.__log.debug('Attempting to queue file: %s', filepath)
        success = self.__queue.append(
            PlaylistItem.create_by_filepath(filepath, filepath) )

        return self.__file_queued( filepath, success, notify)

    def insert(self, position, filepath ):
        self.__log.debug(
            'Attempting to insert %s at position %s', filepath, position )
        return self.__file_queued( filepath, self.__queue.insert( position,
            PlaylistItem.create_by_filepath(filepath, filepath)), True )

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

    def play(self):
        """ This gets called by the player to get
                the last time the file was paused """
        pos = self.__queue.current_item.seek_to
        self.__queue.current_item.seek_to = 0
        return pos

    def pause(self, position):
        """ Called whenever the player is paused """
        self.__queue.current_item.seek_to = position

    def stop(self, position, save_resume_point=True):
        """ This should be run when the program is closed
                or if the user switches playlists """

        self.remove_resume_bookmarks()
        if not self.is_empty and save_resume_point:
            self.__queue.current_item.save_bookmark(
                _('Auto Bookmark'), position, True )

    def skip(self, skip_by=None, skip_to=None, loop=True):
        """ Skip to another track in the playlist.
            Use either skip_by or skip_to, skip_by has precedence.
                skip_to: skip to a known playlist position
                skip_by: skip by n number of episodes (positive or negative)
                loop: loop if the track requested lays out of
                      the 0 to queue_length-1 boundary.
        """
        if not self.__queue:
            return False

        current_item = self.__queue.current_item_position

        if skip_by is not None:
            skip = current_item + skip_by
        elif skip_to is not None:
            skip = skip_to
        else:
            skip = 0
            self.__log.warning('No skip method provided...')

        if not 0 <= skip < self.queue_length:
            self.notify( 'end-of-playlist', loop, caller=self.skip )

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

        self.__queue.current_item_position = skip
        self.__log.debug( 'Skipping to file %d (%s)', skip,
                          self.__queue.current_item.filepath )

        return True

    def get_current_item(self):
        return self.__queue.current_item

    def next(self):
        """ Move the playlist to the next track.
            False indicates end of playlist. """
        return self.skip( skip_by=1, loop=False )

    def prev(self):
        """ Same as next() except moves to the previous track. """
        return self.skip( skip_by=-1, loop=False )


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

        assert isinstance( item, PlaylistItem )
        item.playlist_id = self.playlist_id

        if os.path.isfile(item.filepath) and is_supported(item.filepath):
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

        self[:] = []
        self.playlist_id = None
        self.modified = False
        self.__current_item_position = 0
        self.__mapping_dict = {}

    def get_item(self, item_id):
        return self.__mapping_dict.get(item_id)

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

        if item.bookmarks.count(bookmark_id):
            return item, item.bookmarks[item.bookmarks.index(bookmark_id)]
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

class PlaylistItem(object):
    """ A (hopefully) lightweight object to hold the bare minimum amount of
        data about a single item in a playlist and it's bookmark objects. """

    def __init__(self):
        self.__log = logging.getLogger('panucci.playlist.PlaylistItem')

        self.__filepath = None
        self.__metadata = None
        self.playlist_id = None
        self.duplicate_id = 0
        self.seek_to = 0

        # metadata that's pulled from the playlist file (pls/extm3u)
        self.playlist_reported_filepath = None
        self.playlist_title = None
        self.playlist_length = None

        # a flag to determine whether the item's bookmarks need updating
        # ( used for example, if the duplicate_id is changed )
        self.is_modified = False
        self.bookmarks = []

    def __set_filepath(self, fp):
        if fp != self.__filepath:
            self.__filepath = fp
            self.__metadata = FileMetadata(self.filepath)
            # Don't extract Metadata right away, this makes opening large
            #   playlists _very_ slow. TODO: do this intelligently AND
            #   perhaps del the Metadata object if the file is no longer
            #   being used.
            #self.__metadata.extract_metadata()

    def __get_filepath(self):
        return self.__filepath

    filepath = property( __get_filepath, __set_filepath )

    @staticmethod
    def create_by_filepath(reported_filepath, filepath):
        item = PlaylistItem()
        item.playlist_reported_filepath = reported_filepath
        item.filepath = filepath
        return item

    def __eq__(self, b):
        if isinstance( b, PlaylistItem ):
            return ( self.filepath == b.filepath and
                     self.duplicate_id == b.duplicate_id )
        elif isinstance( b, str ):
            return str(self) == b
        else:
            self.__log.warning('Unsupported comparison: %s', type(b))
            return False

    def __str__(self):
        uid = self.filepath + str(self.duplicate_id)
        return md5(uid).hexdigest()

    @property
    def metadata(self):
        """ Returns a dict of metadata, wooo. """

        metadata = self.__metadata.get_metadata()
        metadata['title'] = self.title
        return metadata

    @property
    def filetype(self):
        return util.detect_filetype(self.filepath)

    def __get_title(self):
        """ Get the title of item, priority is (most important first):
            1. the title given in playlist metadata
            2. the title in the file's metadata (ex. ID3)
            3. a "pretty" version of the filename """

        if self.playlist_title is not None:
            return self.playlist_title
        elif self.__metadata.title:
            return self.__metadata.title
        else:
            return util.pretty_filename(self.filepath)

    # For now set the "playlist_title" because it has highest priority in the
    # __get_title method. We might evenually want to create a separate
    # __custom_title to preserve the playlist_title.
    title = property(__get_title, lambda s,v: setattr(s, 'playlist_title', v))

    @property
    def length(self):
        """ Get the lenght of the item priority is (most important first):
            1. length as reported by mutagen
            2. length found in playlist metadata
            3. otherwise -1 when unknown """

        if self.__metadata.length:
            return self.__metadata.length
        elif self.playlist_length:
            return self.playlist_length
        else:
            return -1

    def load_bookmarks(self):
        self.bookmarks = db.load_bookmarks(
            factory                 = Bookmark().load_from_dict,
            playlist_id             = self.playlist_id,
            bookmark_filepath       = self.filepath,
            playlist_duplicate_id   = self.duplicate_id,
            request_resume_bookmark = None  )

    def save_bookmark(self, name, position, resume_pos=False):
        b = Bookmark()
        b.playlist_id = self.playlist_id
        b.bookmark_name = name
        b.bookmark_filepath = self.filepath
        b.seek_position = position
        b.timestamp = time.time()
        b.is_resume_position = resume_pos
        b.playlist_duplicate_id = self.duplicate_id
        b.save()
        self.bookmarks.append(b)

    def delete_bookmark(self, bookmark_id):
        """ WARNING: if bookmark_id is None, ALL bookmarks will be deleted """
        if bookmark_id is None:
            self.__log.debug( 'Deleting all bookmarks for %s',
                              self.playlist_reported_filepath )

            for bkmk in self.bookmarks:
                bkmk.delete()
        else:
            bkmk = self.bookmarks.index(bookmark_id)
            if bkmk >= 0:
                self.bookmarks[bkmk].delete()
                self.bookmarks.remove(bookmark_id)
            else:
                self.__log.info('Cannot find bookmark with id: %s',bookmark_id)
                return False
        return True

    def update_bookmarks(self):
        for bookmark in self.bookmarks:
            bookmark.playlist_duplicate_id = self.duplicate_id
            bookmark.bookmark_filepath = self.filepath
            db.update_bookmark(bookmark)

class Bookmark(object):
    """ A single bookmark, nothing more, nothing less. """

    def __init__(self):
        self.__log = logging.getLogger('panucci.playlist.Bookmark')

        self.id = 0
        self.playlist_id = None
        self.bookmark_name = ''
        self.bookmark_filepath = ''
        self.seek_position = 0
        self.timestamp = 0
        self.is_resume_position = False
        self.playlist_duplicate_id = 0

    @staticmethod
    def load_from_dict(bkmk_dict):
        bkmkobj = Bookmark()

        for key,value in bkmk_dict.iteritems():
            if hasattr( bkmkobj, key ):
                setattr( bkmkobj, key, value )
            else:
                self.__log.info('Attr: %s doesn\'t exist...', key)

        return bkmkobj

    def save(self):
        self.id = db.save_bookmark(self)
        return self.id

    def delete(self):
        return db.remove_bookmark(self.id)

    def __eq__(self, b):
        if isinstance(b, str):
            return str(self) == b
        elif b is None:
            return False
        else:
            self.__log.warning('Unsupported comparison: %s', type(b))
            return False

    def __str__(self):
        uid =  self.bookmark_filepath
        uid += str(self.playlist_duplicate_id)
        uid += str(self.seek_position)
        return md5(uid).hexdigest()

    def __cmp__(self, b):
        if self.bookmark_filepath == b.bookmark_filepath:
            if self.seek_position == b.seek_position:
                return 0
            else:
                return -1 if self.seek_position < b.seek_position else 1
        else:
            self.__log.info(
                'Can\'t compare bookmarks from different files:\n\tself: %s'
                '\n\tb: %s', self.bookmark_filepath, b.bookmark_filepath )
            return 0

class FileMetadata(object):
    """ A class to hold all information about the file that's currently being
        played. Basically it takes care of metadata extraction... """

    coverart_names = ['cover', 'front', 'albumart', 'back']
    coverart_extensions = ['.png', '.jpg', '.jpeg']
    tag_mappings = {
        'mp4': { '\xa9nam': 'title',
                 '\xa9ART': 'artist',
                 '\xa9alb': 'album',
                 'covr':    'coverart' },
        'mp3': { 'TIT2': 'title',
                 'TPE1': 'artist',
                 'TALB': 'album',
                 'APIC': 'coverart' },
        'ogg': { 'title':  'title',
                 'artist': 'artist',
                 'album':  'album' },
    }
    tag_mappings['m4a']  = tag_mappings['mp4']
    tag_mappings['flac'] = tag_mappings['ogg']

    def __init__(self, filepath):
        self.__log = logging.getLogger('panucci.playlist.FileMetadata')
        self.__filepath = filepath

        self.title = ''
        self.artist = ''
        self.album = ''
        self.length = 0
        self.coverart = None

        self.__metadata_extracted = False

    def extract_metadata(self):
        self.__log.debug('Extracting metadata for %s', self.__filepath)
        filetype = util.detect_filetype(self.__filepath)

        if filetype == 'mp3':
            import mutagen.mp3 as meta_parser
        elif filetype == 'ogg':
            import mutagen.oggvorbis as meta_parser
        elif filetype == 'flac':
            import mutagen.flac as meta_parser
        elif filetype in ['mp4', 'm4a']:
            import mutagen.mp4 as meta_parser
        else:
            self.__log.info(
                'Extracting metadata not supported for %s files.', filetype )
            return False

        try:
            metadata = meta_parser.Open(self.__filepath)
            self.__metadata_extracted = True
        except Exception, e:
            self.title = util.pretty_filename(self.__filepath)
            self.__log.exception('Error running metadata parser...')
            self.__metadata_extracted = False
            return False

        self.length = metadata.info.length * 10**9
        for tag,value in metadata.iteritems():
            if tag.find(':') != -1: # hack for weirdly named coverart tags
                tag = tag.split(':')[0]

            if self.tag_mappings[filetype].has_key(tag):
                if isinstance( value, list ):
                    if len(value):
                        # Here we could either join the list or just take one
                        # item. I chose the latter simply because some ogg
                        # files have several messed up titles...
                        value = value[0]
                    else:
                        continue

                if self.tag_mappings[filetype][tag] != 'coverart':
                    try:
                        value = escape(str(value).strip())
                    except Exception, e:
                        self.__log.exception(
                          'Could not convert tag (%s) to escaped string', tag )
                else:
                    # some coverart classes store the image in the data
                    # attribute whereas others do not :S
                    if hasattr( value, 'data' ):
                        value = value.data

                setattr( self, self.tag_mappings[filetype][tag], value )

        if self.coverart is None:
            self.coverart = self.__find_coverart()

    def __find_coverart(self):
        """ Find coverart in the same directory as the filepath """

        directory = os.path.dirname(self.__filepath)
        for cover in self.__find_coverart_filepath(directory):
            self.__log.debug('Trying to load coverart from %s', cover)
            try:
                f = open(cover,'r')
            except:
                self.__log.exception('Could not open coverart file %s', cover )
                continue

            binary_coverart = f.read()
            f.close()

            if self.__test_coverart(binary_coverart):
                return binary_coverart

        return None

    def __test_coverart(self, data):
        """ tests to see if the file is a proper image file that can be loaded
            into a gtk.gdk.Pixbuf """

        import gtk.gdk
        l = gtk.gdk.PixbufLoader()
        try:
            l.write(data)
            l.close()
            rtn = True
        except:
            rtn = False

        return rtn

    def __find_coverart_filepath(self, directory):
        """ finds the path of potential coverart files """
        dir_filelist = []
        possible_matches = []

        # build the filelist
        for f in os.listdir(directory):
            if os.path.isfile(os.path.join(directory,f)):
                dir_filelist.append(os.path.splitext(f))

        # first pass, check for known filenames
        for f,ext in dir_filelist[:]:
            if f.lower() in self.coverart_names and \
                ext.lower() in self.coverart_extensions:
                possible_matches.append((f,ext))
                dir_filelist.remove((f,ext))

        # second pass, check for known filenames without extensions
        for f,ext in dir_filelist[:]:
            if f.lower() in self.coverart_names and ext == '':
                possible_matches.append((f,ext))
                dir_filelist.remove((f,ext))

        # third pass, check for any image file
        for f,ext in dir_filelist[:]:
            if ext.lower() in self.coverart_extensions:
                possible_matches.append((f,ext))
                dir_filelist.remove((f,ext))

        # yield the results
        for f,ext in possible_matches:
            yield os.path.join( directory, f+ext )

    def get_metadata(self):
        """ Returns a dict of metadata """

        if not self.__metadata_extracted:
            self.extract_metadata()

        metadata = {
            'title':    self.title,
            'artist':   self.artist,
            'album':    self.album,
            'image':    self.coverart,
            'length':   self.length
        }

        return metadata

class PlaylistFile(object):
    """ The base class for playlist file parsers/exporters,
        this should not be used directly but instead subclassed. """

    def __init__(self, filepath, queue):
        self.__log = logging.getLogger('panucci.playlist.PlaylistFile')
        self._filepath = filepath
        self._file = None
        self._items = queue

    def __open_file(self, filepath, mode):
        if self._file is not None:
            self.close_file()

        try:
            self._file = open( filepath, mode )
            self._filepath = filepath
        except Exception, e:
            self._filepath = None
            self._file = None

            self.__log.exception( 'Error opening file: %s', filepath)
            return False

        return True

    def __close_file(self):
        error = False

        if self._file is not None:
            try:
                self._file.close()
            except Exception, e:
                self.__log.exception( 'Error closing file: %s', self.filepath )
                error = True

        self._filepath = None
        self._file = None

        return not error

    def get_absolute_filepath(self, item_filepath):
        if item_filepath is None: return

        if item_filepath.startswith('/'):
            path = item_filepath
        else:
            path = os.path.join(os.path.dirname(self._filepath), item_filepath)

        if os.path.exists( path ):
            return path

    def get_filelist(self):
        return [ item.filepath for item in self._items ]

    def get_filedicts(self):
        dict_list = []
        for item in self._items:
            d = { 'title': item.title,
                  'length': item.length,
                  'filepath': item.filepath }

            dict_list.append(d)
        return dict_list

    def get_queue(self):
        return self._items

    def export_items(self, filepath=None):
        if filepath is not None:
            self._filepath = filepath

        if self.__open_file(filepath, 'w'):
            self.export_hook(self._items)
            self.__close_file()
            return True
        else:
            return False

    def export_hook(self, playlist_items):
        pass

    def parse(self, filepath):
        if self.__open_file( filepath, mode='r' ):
            current_line = self._file.readline()
            while current_line:
                self.parse_line_hook( current_line.strip() )
                current_line = self._file.readline()
            self.__close_file()
            self.parse_eof_hook()
        else:
            return False
        return True

    def parse_line_hook(self, line):
        pass

    def parse_eof_hook(self):
        pass

    def _add_playlist_item(self, item):
        path = self.get_absolute_filepath(item.playlist_reported_filepath)
        if path is not None and os.path.isfile(path):
            item.filepath = path
            self._items.append(item)

class M3U_Playlist(PlaylistFile):
    """ An (extended) m3u parser/writer """

    def __init__(self, *args):
        self.__log = logging.getLogger('panucci.playlist.M3U_Playlist')
        PlaylistFile.__init__( self, *args )
        self.extended_m3u = False
        self.current_item = PlaylistItem()

    def parse_line_hook(self, line):
        if line.startswith('#EXTM3U'):
            self.extended_m3u = True
        elif self.extended_m3u and line.startswith('#EXTINF'):
            match = re.match('#EXTINF:([^,]+),(.*)', line)
            if match is not None:
                length, title = match.groups()
                try: length = int(length)
                except: length = -1
                self.current_item.playlist_length = length
                self.current_item.playlist_title = title
        elif line.startswith('#'):
            pass # skip comments
        elif line:
            path = self.get_absolute_filepath( line )
            if path is not None:
                if os.path.isfile( path ):
                    self.current_item.playlist_reported_filepath = line
                    self._add_playlist_item(self.current_item)
                    self.current_item = PlaylistItem()
                elif os.path.isdir( path ):
                    files = os.listdir( path )
                    files.sort()
                    for file in files:
                        item = PlaylistItem()
                        item.playlist_reported_filepath=os.path.join(line,file)
                        self._add_playlist_item(item)

    def export_hook(self, playlist_items):
        self._file.write('#EXTM3U\n\n')

        for item in playlist_items:
            string = ''
            if not ( item.length is None and item.title is None ):
                length = -1 if item.length is None else int(item.length)
                title = '' if item.title is None else item.title
                string += '#EXTINF:%d,%s\n' % ( length, title )

            string += '%s\n' % item.filepath
            self._file.write(string)

class PLS_Playlist(PlaylistFile):
    """ A somewhat simple pls parser/writer """

    def __init__(self, *args):
        self.__log = logging.getLogger('panucci.playlist.PLS_Playlist')
        PlaylistFile.__init__( self, *args )
        self.current_item = PlaylistItem()
        self.in_playlist_section = False
        self.current_item_number = None

    def __add_current_item(self):
        self._add_playlist_item(self.current_item)

    def parse_line_hook(self, line):
        sect_regex = '\[([^\]]+)\]'
        item_regex = '[^\d]+([\d]+)=(.*)'

        if re.search(item_regex, line) is not None:
            current = re.search(item_regex, line).group(1)
            if self.current_item_number is None:
                self.current_item_number = current
            elif self.current_item_number != current:
                self.__add_current_item()

                self.current_item = PlaylistItem()
                self.current_item_number = current

        if re.search(sect_regex, line) is not None:
            section = re.match(sect_regex, line).group(1).lower()
            self.in_playlist_section = section == 'playlist'
        elif not self.in_playlist_section:
            pass # don't do anything if we're not in [playlist]
        elif line.lower().startswith('file'):
            self.current_item.playlist_reported_filepath = re.search(
                item_regex, line).group(2)
        elif line.lower().startswith('title'):
            self.current_item.playlist_title = re.search(
                                                    item_regex, line).group(2)
        elif line.lower().startswith('length'):
            try: length = int(re.search(item_regex, line).group(2))
            except: length = -1
            self.current_item.playlist_length = length

    def parse_eof_hook(self):
        self.__add_current_item()

    def export_hook(self, playlist_items):
        self._file.write('[playlist]\n')
        self._file.write('NumberOfEntries=%d\n\n' % len(playlist_items))

        for i,item in enumerate(playlist_items):
            title = '' if item.title is None else item.title
            length = -1 if item.length is None else item.length
            self._file.write('File%d=%s\n' % (i+1, item.filepath))
            self._file.write('Title%d=%s\n' % (i+1, title))
            self._file.write('Length%d=%s\n\n' % (i+1, length))

        self._file.write('Version=2\n')


