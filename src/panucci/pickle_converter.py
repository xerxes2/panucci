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

import os.path
import pickle
import shutil
import time
import logging

from dbsqlite import db
from playlist import Bookmark

_ = lambda s: s
log = logging.getLogger('panucci.pickle_converter')

def load_pickle_file( pfile, create_backup=True ):
    try:
        f = open( pfile, 'r' )
    except Exception, e:
        log.exception('Can\'t open pickle file: %s', pfile)
        return False

    try:
        d = pickle.load(f)
    except:
        log.exception('Can\'t load data from pickle file: %s', pfile)
        return False

    f.close()

    for f, data in d.iteritems():
        if f is None or not f:
            continue

        if not data.has_key('bookmarks'):
            data['bookmarks'] = []

        if data.has_key('position'):
            data['bookmarks'].append(
                ( _('Auto Bookmark'), data.get('position', 0)) )

        playlist_id = db.get_playlist_id( f, create_new=True )

        for name, position in data['bookmarks']:
            b = Bookmark()
            b.playlist_id = playlist_id
            b.bookmark_filepath = f
            b.timestamp = time.time()
            b.bookmark_name = name
            b.seek_position = position
            b.is_resume_position = name == _('Auto Bookmark')
            db.save_bookmark(b)

    if create_backup:
        shutil.move( pfile, pfile + '.bak' )

    return True

