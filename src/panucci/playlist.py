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
import glob
import re

import util
from util import log
from dbsqlite import db
from simplegconf import gconf

_ = lambda x: x

class Playlist(object):
    def __init__(self):
        self.filename = None
        self.queue_modified = False

        self._current_file = 0
        self.__current_fileobj = None
        self.__filelist = []
        self.__bookmarks = {}
        self.__bookmarks_model = None
        self.__bookmarks_model_changed = True

    def insert( self, position, filepath ):
        if os.path.isfile(filepath) and util.is_supported(filepath):
            self.__filelist.insert( position, filepath )
            self.__generate_per_file_bookmarks()
            self.__bookmarks_model_changed = True
            self.queue_modified = True
            return True
        else:
            log('File not found or not supported: %s' % filepath)
            return False

    def append( self, filepath ):
        """ Append a file to the queue """
        return self.insert( self.queue_length(), filepath )

    def reset_playlist(self):
        """ clears all the files in the filelist """
        self.__init__()

    @property
    def current_filepath(self):
        """ Get the current file """
        if self._current_file >= self.queue_length():
            log('Current file is greater than queue length, setting to 0.')
            self._current_file = 0

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

    def save_to_new_playlist(self, filepath, playlist_type='m3u'):
        self.filename = filepath
        self.__bookmarks_model_changed = True

        playlist = { 'm3u': M3U_Playlist, 'pls': PLS_Playlist }
        if not playlist.has_key(playlist_type):
            playlist_type = 'm3u'
            self.filename += '.m3u'

        playlist = playlist[playlist_type]()
        playlist.import_filelist(self.__filelist)
        if not playlist.export(filepath=filepath):
            return False

        # copy the bookmarks over to new playlist
        db.remove_all_bookmarks(self.filename)
        bookmarks = self.__bookmarks.copy()
        self.__bookmarks.clear()

        for bookmark in bookmarks.itervalues():
            if bookmark.id >= 0:
                bookmark.playlist_filepath = self.filename
                bookmark.id = db.save_bookmark(bookmark)
                self.append_bookmark(bookmark)
        
        return True

    def save_temp_playlist(self):
        filepath = gconf.sget('temp_playlist', str, '~/.panucci.m3u')
        filepath = os.path.expanduser(filepath)
        return self.save_to_new_playlist(filepath)

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
        return True

    def remove_bookmark( self, bookmark_id ):
        if self.__bookmarks.has_key(bookmark_id):
            db.remove_bookmark( bookmark_id )
            self.__bookmarks_model_changed = True
            del self.__bookmarks[bookmark_id]

    def generate_bookmark_model(self, include_resume_marks=False):
        self.__bookmarks_model = gtk.ListStore(
            gobject.TYPE_INT64, gobject.TYPE_STRING, gobject.TYPE_STRING )

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

    def __remove_per_file_bookmarks(self):
        bookmarks = self.__bookmarks.keys()
        for bmark in bookmarks:
            if bmark < 0:
                del self.__bookmarks[bmark]

    def __generate_per_file_bookmarks(self):
        self.__remove_per_file_bookmarks()
        self.__create_per_file_bookmarks()

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

        # don't include the temporary playlist in the file list
        temp_playlist = gconf.sget('temp_playlist', str, '~/.panucci.m3u')
        temp_playlist = os.path.expanduser(temp_playlist)
        if temp_playlist in files:
            files.remove(temp_playlist)

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
        log('Attempting to load %s' % File)

        error = False
        self.reset_playlist()
        self.filename = File

        parsers = { 'm3u': M3U_Playlist, 'pls': PLS_Playlist }
        extension = util.detect_filetype(File)
        if parsers.has_key(extension):
            log('Loading playlist file (%s)' % extension)
            parser = parsers[extension]()

            if parser.parse(File):
                for f in parser.get_filelist(): self.append(f)
            else:
                return False
        else:
            error = not self.single_file_import(File)

        bookmarks = db.load_bookmarks( self.filename,
            factory=Bookmark().load_from_dict )

        self.__bookmarks = dict([ [b.id, b] for b in bookmarks ])
        self.__create_per_file_bookmarks()

        for id, bkmk in self.__bookmarks.iteritems():
            if bkmk.is_resume_position:
                log('Found resume position, loading bookmark...')
                self.load_from_bookmark( bkmk )
                break

        self.queue_modified = False
        return not error

    def single_file_import( self, filename ):
        """ Add a single track to the playlist """
        self.reset_playlist()
        self.filename = filename
        return self.append( filename )

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
                tag = tag.lower().strip()
                if   tag == 'title':  self.title = str(value)
                elif tag == 'album':  self.album = str(value)
                elif tag == 'artist': self.artist = str(value)

        if not self.title.strip():
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


class PlaylistItem(object):
    def __init__(self, filepath=None, title=None, length=None):
        self.filepath = filepath
        self.title = title
        self.length = length

class PlaylistFile(object):
    def __init__(self):
        self._filepath = None
        self._file = None
        self._items = []

    def __open_file(self, filepath, mode):
        if self._file is not None:
            self.close_file()

        try:
            self._file = open( filepath, mode )
            self._filepath = filepath
        except Exception, e:
            self._filepath = None
            self._file = None

            log( 'Error opening file: %s' % filepath, exception=e )
            return False
    
        return True

    def __close_file(self):
        error = False

        if self._file is not None:
            try:
                self._file.close()
            except Exception, e:
                log( 'Error closing file: %s' % self.filepath, exception=e )
                error = True

        self._filepath = None
        self._file = None

        return not error

    def get_absolute_filepath(self, item_filepath):
        if item_filepath is None: return

        if item_filepath.startswith('/'):
            path = item_filepath
        else:
            path = os.path.join(os.path.dirname(self._filepath),item_filepath)

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

    def import_filelist(self, filelist):
        for f in filelist:
            self._items.append(PlaylistItem(filepath=f))

    def export(self, filepath=None, playlist_items=None):
        if filepath is not None:
            self._filepath = filepath

        if playlist_items is not None:
            self._items = playlist_items

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

class M3U_Playlist(PlaylistFile):
    def __init__(self):
        PlaylistFile.__init__( self )
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
                except: pass
                self.current_item.length = length
                self.current_item.title = title
        elif line.startswith('#'):
            pass # skip comments
        elif line:
            path = self.get_absolute_filepath( line )
            if path is not None:
                if os.path.isfile( path ) and util.is_supported( path ):
                    self.current_item.filepath = path
                    self._items.append(self.current_item)
                    self.current_item = PlaylistItem()
                elif os.path.isdir( path ):
                    files = glob.glob( path + '/*' )
                    for file in files:
                        if os.path.isfile(file) and util.is_supported(file):
                            self._items.append(PlaylistItem(filepath=file))

    def export_hook(self, playlist_items):
        self._file.write('#EXTM3U\n\n')

        for item in playlist_items:
            string = ''
            if not ( item.length is None and item.title is None ):
                length = -1 if item.length is None else item.length
                title = '' if item.title is None else item.title
                string += '#EXTINF:%d,%s\n' % ( length, title )
                
            string += '%s\n' % item.filepath
            self._file.write(string)

class PLS_Playlist(PlaylistFile):
    def __init__(self):
        PlaylistFile.__init__( self )
        self.current_item = PlaylistItem()
        self.in_playlist_section = False
        self.current_item_number = None

    def __add_current_item(self):
        path = self.get_absolute_filepath(self.current_item.filepath)
        if path is not None and os.path.isfile(path): 
            self._items.append(self.current_item)

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
            self.current_item.filepath = re.search(item_regex, line).group(2)
        elif line.lower().startswith('title'):
            self.current_item.title = re.search(item_regex, line).group(2)
        elif line.lower().startswith('length'):
            try: length = int(re.search(item_regex, line).group(2))
            except: pass
            self.current_item.length = length

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


