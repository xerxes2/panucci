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
# _Heavily_ inspired by gPodder's dbsqlite
#

try:
    from sqlite3 import dbapi2 as sqlite
except ImportError:
    log( 'Error importing sqlite, FAIL!')

import os.path
from simplegconf import gconf
from util import log

class Storage(object):
    def __init__(self, db_file):
        """ db_file is the on-disk location of the database file """
        self.__db_file = db_file
        self.__db = None

    @property
    def db(self):
        if self.__db is None:
            self.__db = sqlite.connect(self.__db_file)
            log('Connected to %s' % self.__db_file)
            self.__check_schema()
        return self.__db

    def cursor(self):
        return self.db.cursor()

    def commit(self):
        try:
            log("COMMIT")
            self.db.commit()
        except ProgrammingError, e:
            log('Error commiting changes: %s' % e)

    def __check_schema(self):
        """
        Creates all necessary tables and indexes that don't exist.
        """
        cursor = self.cursor()

        cursor.execute(
        """ CREATE TABLE IF NOT EXISTS bookmarks (
                bookmark_id INTEGER PRIMARY KEY AUTOINCREMENT,
                bookmark_name TEXT,
                playlist_filepath TEXT,
                playlist_index INTEGER,
                seek_position INTEGER,
                timestamp INTEGER,
                is_resume_position INTEGER
            ) """ )

        cursor.close()

    def get_bookmarks(self, playlist_filepath):
        cursor = self.cursor()
        sql = 'SELECT * FROM bookmarks WHERE playlist_filepath = ?'
        cursor.execute( sql, [playlist_filepath,] )
        bookmarks = cursor.fetchall()
        cursor.close()
        return bookmarks

    def bookmark_exists(self, playlist_filepath):
        return self.get_bookmarks( playlist_filepath ) is not None

    def load_bookmarks(self, playlist_filepath, factory=None):
        bkmks = self.get_bookmarks( playlist_filepath )

        if bkmks is None:
            return []

        bkmk_list = []
        for bkmk in bkmks:
            BKMK = {
                'playlist_filepath' : playlist_filepath,
                'id'                : bkmk[0],
                'bookmark_name'     : bkmk[1],
                'playlist_index'    : bkmk[3],
                'seek_position'     : bkmk[4],
                'timestamp'         : bkmk[5],
                'is_resume_position': bool(bkmk[6]),
            }

            if factory is not None:
                BKMK = factory(BKMK)

            bkmk_list.append(BKMK)

        return bkmk_list

    def save_bookmark(self, bookmark):
        if bookmark.id < 0:
            log('Not saving bookmark with negative id (%d)' % bookmark.id)
            return bookmark.id

        if bookmark.playlist_filepath is None:
            log('Not saving bookmark without playlist filepath')
            return bookmark.id

        if bookmark.is_resume_position:
            self.remove_resume_bookmark( bookmark.playlist_filepath )

        log('Saving %s (%s)' % (
            bookmark.bookmark_name, bookmark.playlist_filepath ))

        cursor = self.cursor()
        cursor.execute(
            """ INSERT INTO bookmarks (
                bookmark_name,
                playlist_filepath,
                playlist_index,
                seek_position,
                timestamp,
                is_resume_position
                ) VALUES (?, ?, ?, ?, ?, ?) """,

            ( bookmark.bookmark_name, bookmark.playlist_filepath,
            bookmark.playlist_index, bookmark.seek_position,
            bookmark.timestamp, bookmark.is_resume_position ))

        r_id = self.__get__( 'SELECT last_insert_rowid()' )

        cursor.close()
        self.commit()

        return r_id[0]

    def update_bookmark(self, bookmark):
        log('Updating %s (%s)' % (
            bookmark.bookmark_name, bookmark.playlist_filepath ))

        cursor = self.cursor()
        cursor.execute(
            """ UPDATE bookmarks SET
                bookmark_name = ?,
                playlist_filepath = ?,
                playlist_index = ?,
                seek_position = ?,
                timestamp = ?,
                is_resume_position = ?
                WHERE bookmark_id = ? """,

            ( bookmark.bookmark_name, bookmark.playlist_filepath,
            bookmark.playlist_index, bookmark.seek_position,
            bookmark.timestamp, bookmark.is_resume_position, bookmark.id ))

        cursor.close()
        self.commit()

    def remove_bookmark(self, bookmark_id):
        log('Deleting bookmark by id: %s' % bookmark_id)
        assert bookmark_id >= 0

        cursor = self.cursor()
        cursor.execute(
            'DELETE FROM bookmarks WHERE bookmark_id = ?', (bookmark_id,) )

        cursor.close()
        self.commit()

    def remove_resume_bookmark(self, playlist_filepath):
        log('Deleting resume bookmark for: %s' % playlist_filepath)

        cursor = self.cursor()
        cursor.execute(
            """ DELETE FROM bookmarks WHERE
                playlist_filepath = ? AND
                is_resume_position = 1 """,

            ( playlist_filepath, ))

        cursor.close()
        self.commit()

    def remove_all_bookmarks(self, playlist_filepath):
        log('Deleting all bookmarks for: %s' % playlist_filepath)

        cursor = self.cursor()
        cursor.execute(
            """ DELETE FROM bookmarks WHERE
                playlist_filepath = ? """,

            ( playlist_filepath, ))

        cursor.close()
        self.commit()

    def get_latest_files(self):
        log('Finding latest files...')
        cursor = self.cursor()

        cursor.execute(
            """ SELECT playlist_filepath FROM bookmarks 
                WHERE is_resume_position = 1
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

db = Storage(os.path.expanduser(gconf.sget('db_location', str, '~/.panucci.sqlite')))

