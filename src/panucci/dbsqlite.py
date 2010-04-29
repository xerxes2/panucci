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
# _Heavily_ inspired by gPodder's dbsqlite
#

from __future__ import absolute_import

import os.path
import logging
import string
import time

log = logging.getLogger('panucci.dbsqlite')

try:
    from sqlite3 import dbapi2 as sqlite
except ImportError:
    log.critical('Error importing sqlite, FAIL!')

import panucci

class Storage(object):
    def __init__(self, db_file):
        """ db_file is the on-disk location of the database file """
        self.__db_file = db_file
        self.__db = None
        self.__log = logging.getLogger('panucci.dbsqlite.Storage')

    @property
    def db(self):
        if self.__db is None:
            self.__db = sqlite.connect(self.__db_file)
            self.__db.text_factory = str
            self.__log.debug('Connected to %s', self.__db_file)
            self.__check_schema()
        return self.__db

    def cursor(self):
        return self.db.cursor()

    def commit(self):
        try:
            self.__log.debug('COMMIT')
            self.db.commit()
        except ProgrammingError, e:
            self.__log.error('Error commiting changes!', exc_info=1)

    def __check_schema(self):
        """
        Creates all necessary tables and indexes that don't exist.
        """
        cursor = self.cursor()

        cursor.execute(
        """ CREATE TABLE IF NOT EXISTS bookmarks (
                bookmark_id INTEGER PRIMARY KEY AUTOINCREMENT,
                bookmark_name TEXT,
                playlist_id INTEGER,
                bookmark_filepath TEXT,
                seek_position INTEGER,
                timestamp INTEGER,
                is_resume_position INTEGER,
                playlist_duplicate_id INTEGER
            ) """ )

        cursor.execute(
        """ CREATE TABLE IF NOT EXISTS playlists (
                playlist_id INTEGER PRIMARY KEY AUTOINCREMENT,
                filepath TEXT,
                timestamp INTEGER
            ) """ )

        cursor.close()


    #################################
    # Bookmark-related functions

    def get_bookmarks(self, playlist_id=None, bookmark_filepath=None,
        playlist_duplicate_id=None, request_resume_bookmark=None):
        """ Note: the request_resume_bookmark argument will only return resume
                bookmarks if it's set to True. If you don't care whether you're
                getting resume bookmarks or not set it to None """

        sql = 'SELECT * FROM bookmarks'
        conditions = []
        args = []

        if playlist_id is not None:
            conditions.append('playlist_id = ?')
            args.append(playlist_id)

        if bookmark_filepath is not None:
            conditions.append('bookmark_filepath = ?')
            args.append(bookmark_filepath)

        if playlist_duplicate_id is not None:
            conditions.append('playlist_duplicate_id = ?')
            args.append(playlist_duplicate_id)

        if request_resume_bookmark is not None:
            conditions.append('is_resume_position = ?')
            args.append(request_resume_bookmark)

        if conditions:
            sql += ' WHERE '

        sql += string.join(conditions, ' AND ')

        cursor = self.cursor()
        cursor.execute( sql, args )
        bookmarks = cursor.fetchall()
        cursor.close()

        return bookmarks

    def bookmark_exists(self, playlist_id):
        return self.get_bookmarks( playlist_id ) is not None

    def load_bookmarks(self, factory, *args, **kwargs):
        """ Load bookmarks into a dict and return a list of dicts or
                return a list of the outputs from the factory function.
                Set the factory function to None to not use it.
            Note: This is a wrapper around get_bookmarks, see get_bookmarks
                for all available arguments. """

        bkmks = self.get_bookmarks( *args, **kwargs )

        if bkmks is None:
            return []

        bkmk_list = []
        for bkmk in bkmks:
            BKMK = {
                'id'                    : bkmk[0],
                'bookmark_name'         : bkmk[1],
                'playlist_id'           : bkmk[2],
                'bookmark_filepath'     : bkmk[3],
                'seek_position'         : bkmk[4],
                'timestamp'             : bkmk[5],
                'is_resume_position'    : bool(bkmk[6]),
                'playlist_duplicate_id' : bkmk[7],
            }

            if factory is not None:
                BKMK = factory(BKMK)

            bkmk_list.append(BKMK)

        return bkmk_list

    def save_bookmark(self, bookmark):
        if bookmark.id < 0:
            self.__log.warn('Not saving bookmark with negative id (%d)', bookmark.id)
            return bookmark.id

        if bookmark.playlist_id is None:
            self.__log.warn('Not saving bookmark without playlist filepath')
            return bookmark.id

        if bookmark.is_resume_position:
            self.remove_resume_bookmark( bookmark.playlist_id )

        self.__log.info('Saving %s, %d (%s)', bookmark.bookmark_name,
            bookmark.seek_position, bookmark.bookmark_filepath )

        cursor = self.cursor()
        cursor.execute(
            """ INSERT INTO bookmarks (
                bookmark_name,
                playlist_id,
                bookmark_filepath,
                seek_position,
                timestamp,
                is_resume_position,
                playlist_duplicate_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?) """,

            ( bookmark.bookmark_name, bookmark.playlist_id,
            bookmark.bookmark_filepath, bookmark.seek_position,
            bookmark.timestamp, bookmark.is_resume_position,
            bookmark.playlist_duplicate_id ))

        r_id = self.__get__( 'SELECT last_insert_rowid()' )

        cursor.close()
        self.commit()

        return r_id[0]

    def update_bookmark(self, bookmark):
        self.__log.info('Updating %s (%s)',
            bookmark.bookmark_name, bookmark.playlist_id )

        cursor = self.cursor()
        cursor.execute(
            """ UPDATE bookmarks SET
                bookmark_name = ?,
                playlist_id = ?,
                bookmark_filepath = ?,
                seek_position = ?,
                timestamp = ?,
                is_resume_position = ?,
                playlist_duplicate_id = ?
                WHERE bookmark_id = ? """,

            ( bookmark.bookmark_name, bookmark.playlist_id,
            bookmark.bookmark_filepath, bookmark.seek_position,
            bookmark.timestamp, bookmark.is_resume_position,
            bookmark.playlist_duplicate_id, bookmark.id ))

        cursor.close()
        self.commit()

    def remove_bookmark(self, bookmark_id):
        self.__log.info('Deleting bookmark by id: %s', bookmark_id)
        assert bookmark_id >= 0

        cursor = self.cursor()
        cursor.execute(
            'DELETE FROM bookmarks WHERE bookmark_id = ?', (bookmark_id,) )

        cursor.close()
        self.commit()

    def remove_resume_bookmark(self, playlist_id):
        self.__log.info('Deleting resume bookmark for: %s', playlist_id)

        cursor = self.cursor()
        cursor.execute(
            """ DELETE FROM bookmarks WHERE
                playlist_id = ? AND
                is_resume_position = 1 """,

            ( playlist_id, ))

        cursor.close()
        self.commit()

    def remove_all_bookmarks(self, playlist_id):
        self.__log.info('Deleting all bookmarks for: %s', playlist_id)

        cursor = self.cursor()
        cursor.execute(
            """ DELETE FROM bookmarks WHERE
                playlist_id = ? """,

            ( playlist_id, ))

        cursor.close()
        self.commit()


    #################################
    # Playlist-related functions

    def playlist_exists(self, filepath):
        if filepath is not None and filepath:
            return self.__get__( 'SELECT * FROM playlists WHERE filepath = ?',
                filepath ) is not None
        else:
            return False

    def get_playlist_id(self, filepath, create_new=False, update_time=False):
        """ Get a playlist_id by it's filepath
                create_new: if True it will create a new playlist
                    entry if none exists for the filepath.
                update_time: if True it updates the timestamp for the
                    playlist entry of the filepath. """

        if self.playlist_exists(filepath):
            playlist_id = self.__get__(
                'SELECT playlist_id FROM playlists WHERE filepath = ?',
                filepath )[0]
        elif create_new:
            playlist_id = self.add_playlist( filepath )
        else:
            playlist_id = None

        if playlist_id is not None and update_time:
            self.update_playlist( playlist_id, filepath )

        return playlist_id

    def add_playlist(self, filepath, timestamp=None):
        self.__log.info( 'Adding playlist: %s', filepath )

        if timestamp is None:
            timestamp = time.time()

        cursor = self.cursor()
        cursor.execute(
            """ INSERT INTO playlists (filepath, timestamp) VALUES (?,?) """,
            ( filepath, timestamp ) )

        cursor.close()
        self.commit()

        r_id = self.__get__( 'SELECT last_insert_rowid()' )[0]

        return r_id

    def update_playlist(self, playlist_id, filepath, timestamp=None):
        self.__log.info( 'Updating playlist: %s', filepath )

        if timestamp is None:
            timestamp = time.time()

        cursor = self.cursor()
        cursor.execute(
            """ UPDATE playlists SET
                filepath = ?,
                timestamp = ?
                WHERE playlist_id = ? """,

            ( filepath, timestamp, playlist_id ) )

        cursor.close()
        self.commit()

    def delete_playlist(self, playlist_id):
        self.__log.info( 'Deleting playlist: %d', playlist_id )

        cursor = self.cursor()
        cursor.execute(
            """ DELETE FROM playlists WHERE playlist_id = ? """,
            ( playlist_id, ))

        cursor.close()
        self.commit()

    def get_latest_files(self):
        self.__log.debug('Finding latest files...')
        cursor = self.cursor()

        cursor.execute(
            """ SELECT filepath FROM playlists
                ORDER BY timestamp DESC """)

        files = cursor.fetchall()
        cursor.close()

        return [ f[0] for f in files ]


    def __get__(self, sql, params=None):
        """ Returns the first row of a query result """

        cursor = self.cursor()

        if params is None:
            cursor.execute(sql)
        else:
            if not isinstance( params, (list, tuple) ):
                params = [ params, ]

            cursor.execute(sql, params)

        row = cursor.fetchone()
        cursor.close()

        return row

db = Storage(os.path.expanduser(panucci.DATABASE_FILE))

