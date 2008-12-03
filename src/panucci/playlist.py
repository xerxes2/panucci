#!/usr/bin/env python
#
# Copyright (c) 2008 The Panucci Audiobook and Podcast Player Project
# 
# Permission is hereby granted, free of charge, to any person obtaining
# a copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject to
# the following conditions:
# 
# The above copyright notice and this permission notice shall be included
# in all copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
# IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY
# CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
# TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
# SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
# 

import gobject, gtk
import time
import os.path
import hashlib
import mutagen

import util
from util import log
from dbsqlite import db

_ = lambda x: x

class Playlist(object):
    def __init__(self):
        self.filename = None

        self._current_file = 0
        self.__current_fileobj = None
        self.__filelist = []
        self.__bookmarks = {}
        self.__bookmarks_model = None
        self.__bookmarks_model_changed = True

    def insert( self, position, filepath ):
        if os.path.exists(filepath):
            self.__filelist.insert( position, filepath )
        else:
            log('File cannot be found: %s' % filepath)

    def append( self, filepath ):
        """ Append a file to the queue """
        self.insert( self.queue_length(), filepath )

    def reset_playlist(self):
        """ clears all the files in the filelist """
        self.__init__()

    @property
    def current_filepath(self):
        """ Get the current file """
        if self.__filelist:
            return self.__filelist[self._current_file]

    @property
    def current_fileobj(self):
        """ Get the FileObject of the current file """
        if self.__current_fileobj is None or (
                self.__current_fileobj.filepath != self.current_filepath ):
            log('Cached FileObject is out of date, loading a new one')
            self.__current_fileobj = FileObject( self.current_filepath )

        return self.__current_fileobj

    def get_current_file_number(self):
        return self._current_file

    def queue_length(self):
        return len(self.__filelist)

    def is_empty(self):
        """ Returns False if we're at the end of the
                playlist or if no files have been loaded """
        return self.get_current_file_number() >= self.queue_length() 

    def md5( self, string ):
        """ Return the md5sum of 'string' """
        return hashlib.md5(string).hexdigest()

    ######################################
    # Bookmark-related functions
    ######################################

    def append_bookmark(self, bookmark):
        self.__bookmarks[bookmark.id] = bookmark

    def load_from_bookmark( self, bkmk ):
        if self.__bookmarks.has_key(bkmk):
            bookmark = self.__bookmarks[bkmk]
        elif isinstance( bkmk, Bookmark ):
            bookmark = bkmk
        else:
            log('No such bookmark, type: %s' % type(bkmk))
            return

        self._current_file = bookmark.playlist_index
        if self.current_fileobj is not None:
            self.current_fileobj.seek_to = bookmark.seek_position

    def save_bookmark( self, bookmark_name, position ):
        self.__save_bookmark( bookmark_name, position, resume_pos=False )
        self.__bookmarks_model_changed = True

    def __save_bookmark( self, bookmark_name, position, resume_pos=False ):
        b = Bookmark()
        b.playlist_filepath = self.filename
        b.bookmark_name = bookmark_name
        b.playlist_index = self.get_current_file_number()
        b.seek_position = position
        b.timestamp = time.time()
        b.is_resume_position = resume_pos
        b.id = db.save_bookmark(b)
        self.append_bookmark(b)

    def update_bookmark( self, bookmark_id, name=None, seek_position=None ):
        if not self.__bookmarks.has_key(bookmark_id):
            log('No such bookmark id (%s)' % bookmark_id)
            return False

        bookmark = self.__bookmarks[bookmark_id]
        bookmark.timestamp = time.time()

        if name is not None:
            bookmark.bookmark_name = name

        if seek_position is not None:
            bookmark.seek_position = seek_position

        db.update_bookmark(bookmark)

    def remove_bookmark( self, bookmark_id ):
        if self.__bookmarks.has_key(bookmark_id):
            db.remove_bookmark( bookmark_id )
            self.__bookmarks_model_changed = True
            del self.__bookmarks[bookmark_id]

    def generate_bookmark_model(self, include_resume_marks=False):
        self.__bookmarks_model = gtk.ListStore(
            gobject.TYPE_INT64, gobject.TYPE_STRING, gobject.TYPE_STRING )

        self.__create_per_file_bookmarks()

        bookmarks = self.__bookmarks.values()
        bookmarks.sort()

        for bookmark in bookmarks:
            if not bookmark.is_resume_position or (
                bookmark.is_resume_position and include_resume_marks ):

                self.__bookmarks_model.append([
                    bookmark.id, bookmark.bookmark_name,
                    '[%02d - %s] %s' % ( bookmark.playlist_index+1,
                    util.convert_ns(bookmark.seek_position),
                    os.path.basename(self.__filelist[bookmark.playlist_index])
                    ) ])

    def get_bookmark_model(self, include_resume_marks=False):
        if self.__bookmarks_model is None or self.__bookmarks_model_changed:
            log('Generating new bookmarks model')
            self.generate_bookmark_model(include_resume_marks)
            self.__bookmarks_model_changed = False
        else:
            log('Using cached bookmarks model')

        return self.__bookmarks_model

    def __create_per_file_bookmarks(self):
        for n, filepath in enumerate(self.__filelist):
            b = Bookmark()
            b.id = -1*(n+1)
            b.bookmark_name = '%s %d' % (_('File'), n+1)
            b.playlist_index = n
            self.append_bookmark(b)

    ######################################
    # File-related convenience functions
    ######################################

    def get_current_position(self):
        """ Returns the saved position for the current
                file or 0 if no file is available"""
        if self.current_fileobj is not None:
            return self.current_fileobj.seek_to
        else:
            return 0

    def get_estimated_duration(self):
        """ Returns the file's duration as determined by mutagen """
        if self.current_fileobj is not None:
            return int( self.current_fileobj.length * 10**9 )
        else:
            return 0

    def get_current_filetype(self):
        """ Returns the filetype of the current
                file or None if no file is available """

        if self.current_fileobj is not None:
            return self.current_fileobj.filetype

    def get_file_metadata(self):
        """ Return the metadata associated with the current FileObject """
        if self.current_fileobj is not None:
            return self.current_fileobj.get_metadata()
        else:
            return {}

    def get_current_filepath(self):
        if self.current_fileobj is not None:
            return self.current_fileobj.filepath

    def get_recent_files(self, max_files=10):
        files = db.get_latest_files()
        if len(files) > max_files:
            return files[:max_files]
        else:
            return files

    ##################################
    # File importing functions
    ##################################

    def load(self, File):
        """ Detects File's filetype then loads it using
            the appropriate loader function """

        self.reset_playlist()
        self.filename = File

        extension = util.detect_filetype(File)
        if extension == 'm3u':
            self.m3u_importer(File)
        elif extension == 'pls':
            pass
        else:
            self.single_file_import(File)

        bookmarks = db.load_bookmarks( self.filename,
            factory=Bookmark().load_from_dict )

        self.__bookmarks = dict([ [b.id, b] for b in bookmarks ])

        for id, bkmk in self.__bookmarks.iteritems():
            if bkmk.is_resume_position:
                log('Found resume position, loading bookmark...')
                self.load_from_bookmark( bkmk )
                break

    def m3u_importer( self, filename ):
        """ Import an m3u playlist 
            TODO: make this actually support proper m3u playlists... """

        f = open( filename, 'r' )
        files = f.read()
        f.close()

        files = files.splitlines()
        for f in files:
            if f.strip(): self.append(f.strip())

    def single_file_import( self, filename ):
        """ Add a single track to the playlist """
        self.append( filename )

    ##################################
    # Plalist controls
    ##################################

    def play(self):
        """ This gets called by the player to get
                the last time the file was paused """
        return self.current_fileobj.play()

    def pause(self, position):
        """ Called whenever the player is paused """
        self.current_fileobj.pause(position)
        self.__save_bookmark( _('Auto Bookmark'), position, True )

    def stop(self):
        """ Caused when we reach the end of a file """
        db.remove_resume_bookmark( self.filename )
        self.current_fileobj.pause(0)

    def skip(self, skip_by=None, skip_to=None, dont_loop=False):
        """ Skip to another track in the playlist.
            Use either skip_by or skip_to, skip_by has precedence.
                skip_to: skip to a known playlist position
                skip_by: skip by n number of episodes (positive or negative)
                dont_loop: applies only to skip_by, if we're skipping past
                    the last track loop back to the begining.
        """
        if not self.__filelist:
            return False

        if skip_by is not None:
            if dont_loop:
                skip = self._current_file + skip_by
            else:
                skip = ( self._current_file + skip_by ) % self.queue_length()
        elif skip_to is not None:
            skip = skip_to
        else:
            log('No skip method provided...')

        if not ( 0 <= skip < self.queue_length() ):
            log('Can\'t skip to non-existant file. (requested=%d, total=%d)' % (
                skip, self.queue_length()) )
            return False

        self._current_file = skip
        log('Skipping to file %d (%s)' % (skip, self.current_fileobj.filepath) )
        return True

    def next(self):
        """ Move the playlist to the next track.
            False indicates end of playlist. """
        return self.skip( skip_by=1, dont_loop=True )

    def prev(self):
        """ Same as next() except moves to the previous track. """
        return self.skip( skip_by=-1, dont_loop=True )


class Bookmark(object):
    def __init__(self):
        self.id = 0
        self.playlist_filepath = ''
        self.bookmark_name = ''
        self.playlist_index = 0
        self.seek_position = 0
        self.timestamp = 0
        self.is_resume_position = False

    @staticmethod
    def load_from_dict(bkmk_dict):
        bkmkobj = Bookmark()

        for key,value in bkmk_dict.iteritems():
            if hasattr( bkmkobj, key ):
                setattr( bkmkobj, key, value )
            else:
                log('Attr: %s doesn\'t exist...' % key)

        return bkmkobj

    def __cmp__(self, b):
        if self.playlist_index == b.playlist_index:
            if self.seek_position == b.seek_position:
                return 0
            else:
                return -1 if self.seek_position < b.seek_position else 1
        else:
            return -1 if self.playlist_index < b.playlist_index else 1


class FileObject(object):
    coverart_names = ['cover', 'cover.jpg']

    def __init__(self, filepath):
        self.filepath = filepath  # the full path to the file
        self.seek_to = 0

        self.title = ''
        self.artist = ''
        self.album = ''
        self.length = 0
        self.coverart = None

        self.__metadata_extracted = False

    def extract_metadata(self):
        filetype = util.detect_filetype(self.filepath)
        File = mutagen.File(self.filepath)
        self.length = File.info.length

        if filetype == 'mp3':
            for tag,value in File.iteritems():
                if   tag == 'TIT2': self.title = str(value)
                elif tag == 'TALB': self.album = str(value)
                elif tag == 'TPE1': self.artist = str(value)
                elif tag.startswith('APIC'): self.coverart = value.data

        elif filetype in ['ogg', 'flac']:
            for tag,value in File.iteritems():
                if   tag == 'title':  self.title = str(value)
                elif tag == 'album':  self.album = str(value)
                elif tag == 'artist': self.artist = str(value)

        else:
            self.title = util.pretty_filename(self.filepath)

        if self.coverart is None:
            self.coverart = self.__find_coverart()

    def __find_coverart(self):
        """ Find coverart in the same directory as the filepath """
        directory = os.path.dirname(self.filepath)
        for cover in self.coverart_names:
            c = os.path.join( directory, cover )
            if os.path.isfile(c):
                try:
                    f.open(c,'r')
                    binary_coverart = f.read()
                    f.close()
                    return binary_coverart
                except:
                    pass
        return None

    def get_metadata(self):
        """ Returns a dict of metadata """

        if not self.__metadata_extracted:
            log('Extracting metadata for %s' % self.filepath)
            self.extract_metadata()
            self.__metadata_extracted = True

        metadata = { 
            'title':    self.title,
            'artist':   self.artist,
            'album':    self.album,
            'image':    self.coverart,
        }

        return metadata

    @property
    def filetype(self):
        return util.detect_filetype(self.filepath)

    def play(self):
        return max(0, self.seek_to)

    def pause(self, position):
        self.seek_to = position

