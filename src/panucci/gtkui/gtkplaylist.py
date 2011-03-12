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
#
# Based on http://thpinfo.com/2008/panucci/:
#  A resuming media player for Podcasts and Audiobooks
#  Copyright (c) 2008-05-26 Thomas Perl <thpinfo.com>
#  (based on http://pygstdocs.berlios.de/pygst-tutorial/seeking.html)

from __future__ import absolute_import

import logging
import sys
import os, os.path
import time

import gtk
import gobject
import pango

import cgi
import dbus

import panucci
from panucci import platform
from panucci import util
from panucci.gtkui import gtkutil

##################################################
# PlaylistTab
##################################################
class PlaylistTab(gtk.VBox):
    def __init__(self, main_window, player):
        gtk.VBox.__init__(self)
        self.__log = logging.getLogger('panucci.panucci.BookmarksWindow')
        self.main = main_window
        self.player = player

        self.__model = gtk.TreeStore(
            # uid, name, position
            gobject.TYPE_STRING, gobject.TYPE_STRING, gobject.TYPE_STRING )

        self.set_spacing(5)
        self.treeview = gtk.TreeView()
        self.treeview.set_model(self.__model)
        self.treeview.set_headers_visible(True)
        tree_selection = self.treeview.get_selection()
        # This breaks drag and drop, only use single selection for now
        # tree_selection.set_mode(gtk.SELECTION_MULTIPLE)
        tree_selection.connect('changed', self.tree_selection_changed)

        # The tree lines look nasty on maemo
        if platform.DESKTOP:
            self.treeview.set_enable_tree_lines(True)
        self.update_model()

        ncol = gtk.TreeViewColumn(_('Name'))
        ncell = gtk.CellRendererText()
        ncell.set_property('ellipsize', pango.ELLIPSIZE_END)
        ncell.set_property('editable', True)
        ncell.connect('edited', self.label_edited)
        ncol.set_expand(True)
        ncol.pack_start(ncell)
        ncol.add_attribute(ncell, 'text', 1)

        tcol = gtk.TreeViewColumn(_('Position'))
        tcell = gtk.CellRendererText()
        tcol.pack_start(tcell)
        tcol.add_attribute(tcell, 'text', 2)

        self.treeview.append_column(ncol)
        self.treeview.append_column(tcol)
        self.treeview.connect('drag-data-received', self.drag_data_recieved)
        self.treeview.connect('drag_data_get', self.drag_data_get_data)

        treeview_targets = [
            ( 'playlist_row_data', gtk.TARGET_SAME_WIDGET, 0 ) ]

        self.treeview.enable_model_drag_source(
            gtk.gdk.BUTTON1_MASK, treeview_targets, gtk.gdk.ACTION_COPY )

        self.treeview.enable_model_drag_dest(
            treeview_targets, gtk.gdk.ACTION_COPY )

        sw = gtk.ScrolledWindow()
        sw.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        sw.set_shadow_type(gtk.SHADOW_IN)
        sw.add(self.treeview)
        self.add(sw)

        self.hbox = gtk.HBox()

        self.add_button = gtk.Button(gtk.STOCK_NEW)
        self.add_button.set_use_stock(True)
        gtkutil.set_stock_button_text( self.add_button, _('Add File') )
        self.add_button.connect('clicked', self.add_file)
        self.hbox.pack_start(self.add_button, True, True)

        self.dir_button = gtk.Button(gtk.STOCK_OPEN)
        self.dir_button.set_use_stock(True)
        gtkutil.set_stock_button_text( self.dir_button, _('Add Folder') )
        self.dir_button.connect('clicked', self.add_directory)
        self.hbox.pack_start(self.dir_button, True, True)

        self.remove_button = gtk.Button(stock=gtk.STOCK_REMOVE)
        self.remove_button.connect('clicked', self.remove_bookmark)
        self.hbox.pack_start(self.remove_button, True, True)

        self.jump_button = gtk.Button(stock=gtk.STOCK_JUMP_TO)
        self.jump_button.connect('clicked', self.jump_bookmark)
        self.hbox.pack_start(self.jump_button, True, True)

        if platform.FREMANTLE:
            self.info_button = gtk.Button(_('Info'))
        else:
            self.info_button = gtk.Button(stock=gtk.STOCK_INFO)

        self.info_button.connect('clicked', self.show_playlist_item_details)
        self.hbox.pack_start(self.info_button, True, True)

        if platform.FREMANTLE:
            self.empty_button = gtk.Button(_('Clear'))
        else:
            self.empty_button = gtk.Button(stock=gtk.STOCK_DELETE)
        self.empty_button.connect('clicked', self.empty_playlist)
        self.hbox.pack_start(self.empty_button, True, True)

        if platform.FREMANTLE:
            for child in self.hbox.get_children():
                if isinstance(child, gtk.Button):
                    child.set_name('HildonButton-thumb')
            self.hbox.set_size_request(-1, 105)

        self.pack_start(self.hbox, False, True)

        self.player.playlist.register( 'file_queued',
                                  lambda x,y,z: self.update_model() )
        self.player.playlist.register( 'bookmark_added', self.on_bookmark_added )

        self.show_all()

    def tree_selection_changed(self, treeselection):
        count = treeselection.count_selected_rows()
        self.remove_button.set_sensitive(count > 0)
        self.jump_button.set_sensitive(count == 1)
        self.info_button.set_sensitive(count == 1)

    def drag_data_get_data(
        self, treeview, context, selection, target_id, timestamp):

        treeselection = treeview.get_selection()
        model, iter = treeselection.get_selected()
        # only allow moving around top-level parents
        if model.iter_parent(iter) is None:
            # send the path of the selected row
            data = model.get_string_from_iter(iter)
            selection.set(selection.target, 8, data)
        else:
            self.__log.debug("Can't move children...")

    def drag_data_recieved(
        self, treeview, context, x, y, selection, info, timestamp):

        drop_info = treeview.get_dest_row_at_pos(x, y)

        # TODO: If user drags the row past the last row, drop_info is None
        #       I'm not sure if it's safe to simply assume that None is
        #       euqivalent to the last row...
        if None not in [ drop_info and selection.data ]:
            model = treeview.get_model()
            path, position = drop_info

            from_iter = model.get_iter_from_string(selection.data)

            # make sure the to_iter doesn't have a parent
            to_iter = model.get_iter(path)
            if model.iter_parent(to_iter) is not None:
                to_iter = model.iter_parent(to_iter)

            from_row = model.get_path(from_iter)[0]
            to_row = path[0]

            if ( position == gtk.TREE_VIEW_DROP_BEFORE or
                 position == gtk.TREE_VIEW_DROP_INTO_OR_BEFORE ):
                model.move_before( from_iter, to_iter )
                to_row = to_row - 1 if from_row < to_row else to_row
            elif ( position == gtk.TREE_VIEW_DROP_AFTER or
                 position == gtk.TREE_VIEW_DROP_INTO_OR_AFTER ):
                model.move_after( from_iter, to_iter )
                to_row = to_row + 1 if from_row > to_row else to_row
            else:
                self.__log.debug('Drop not supported: %s', position)

            # don't do anything if we're not actually moving rows around
            if from_row != to_row:
                self.player.playlist.move_item( from_row, to_row )

        else:
            self.__log.debug('No drop_data or selection.data available')

    def update_model(self):
        plist = self.player.playlist
        path_info = self.treeview.get_path_at_pos(0,0)
        path = path_info[0] if path_info is not None else None

        self.__model.clear()

        # build the tree
        for item, data in plist.get_playlist_item_ids():
            parent = self.__model.append(None, (item, data.get('title'), None))

            for bid, bname, bpos in plist.get_bookmarks_from_item_id( item ):
                nice_bpos = util.convert_ns(bpos)
                self.__model.append( parent, (bid, bname, nice_bpos) )

        self.treeview.expand_all()

        if path is not None:
            self.treeview.scroll_to_cell(path)

    def label_edited(self, cellrenderer, path, new_text):
        iter = self.__model.get_iter(path)
        old_text = self.__model.get_value(iter, 1)

        if new_text.strip() and old_text != new_text:
            # this loop will only run once, because only one cell can be
            # edited at a time, we use it to get the item and bookmark ids
            for m, bkmk_id, biter, item_id, iiter in self.__cur_selection():
                self.__model.set_value(iter, 1, new_text)
                self.player.playlist.update_bookmark(
                    item_id, bkmk_id, name=new_text )
        else:
            self.__model.set_value(iter, 1, old_text)

    def on_bookmark_added(self, parent_id, bookmark_name, position):
        self.main.notify(_('Bookmark added: %s') % bookmark_name)
        self.update_model()

    def add_file(self, widget):
        filename = gtkutil.get_file_from_filechooser(self.main)
        if filename is not None:
            self.player.playlist.load(filename)

    def add_directory(self, widget):
        directory = gtkutil.get_file_from_filechooser(self.main, folder=True )
        if directory is not None:
            self.player.playlist.load(directory)

    def __cur_selection(self):
        selection = self.treeview.get_selection()
        model, bookmark_paths = selection.get_selected_rows()

        # Convert the paths to gtk.TreeRowReference objects, because we
        # might modify the model while this generator is running
        bookmark_refs = [gtk.TreeRowReference(model, p) for p in bookmark_paths]

        for reference in bookmark_refs:
            bookmark_iter = model.get_iter(reference.get_path())
            item_iter = model.iter_parent(bookmark_iter)

            # bookmark_iter is actually an item_iter
            if item_iter is None:
                item_iter = bookmark_iter
                item_id = model.get_value(item_iter, 0)
                bookmark_id, bookmark_iter = None, None
            else:
                bookmark_id = model.get_value(bookmark_iter, 0)
                item_id = model.get_value(item_iter, 0)

            yield model, bookmark_id, bookmark_iter, item_id, item_iter

    def remove_bookmark(self, w=None):
        for model, bkmk_id, bkmk_iter, item_id, item_iter in self.__cur_selection():
            self.player.playlist.remove_bookmark( item_id, bkmk_id )
            if bkmk_iter is not None:
                model.remove(bkmk_iter)
            elif item_iter is not None:
                model.remove(item_iter)

    def select_current_item(self):
        model = self.treeview.get_model()
        selection = self.treeview.get_selection()
        current_item_id = str(self.player.playlist.get_current_item())
        for row in iter(model):
            if model.get_value(row.iter, 0) == current_item_id:
                selection.unselect_all()
                self.treeview.set_cursor(row.path)
                self.treeview.scroll_to_cell(row.path, use_align=True)
                break

    def show_playlist_item_details(self, w):
        selection = self.treeview.get_selection()
        if selection.count_selected_rows() == 1:
            selected = self.__cur_selection().next()
            model, bkmk_id, bkmk_iter, item_id, item_iter = selected
            playlist_item = self.player.playlist.get_item_by_id(item_id)
            PlaylistItemDetails(self.main, playlist_item)

    def jump_bookmark(self, w):
        selected = list(self.__cur_selection())
        if len(selected) == 1:
            # It should be guranteed by the fact that we only enable the
            # "Jump to" button when the selection count equals 1.
            model, bkmk_id, bkmk_iter, item_id, item_iter = selected.pop(0)
            self.player.playlist.load_from_bookmark_id(item_id, bkmk_id)

            # FIXME: The player/playlist should be able to take care of this

    def empty_playlist(self, w):
        self.player.playlist.reset_playlist()
        self.treeview.get_model().clear()

##################################################
# PlaylistItemDetails
##################################################
class PlaylistItemDetails(gtk.Dialog):
    def __init__(self, main, playlist_item):
        gtk.Dialog.__init__(self, _('Playlist item details'),
                            main.main_window, gtk.DIALOG_MODAL)

        if not platform.FREMANTLE:
            self.add_button(gtk.STOCK_CLOSE, gtk.RESPONSE_OK)

        self.main = main
        self.fill(playlist_item)
        self.set_has_separator(False)
        self.set_resizable(False)
        self.show_all()
        self.run()
        self.destroy()

    def fill(self, playlist_item):
        t = gtk.Table(10, 2)
        self.vbox.pack_start(t, expand=False)

        metadata = playlist_item.metadata

        t.attach(gtk.Label(_('Custom title:')), 0, 1, 0, 1)
        t.attach(gtk.Label(_('ID:')), 0, 1, 1, 2)
        t.attach(gtk.Label(_('Playlist ID:')), 0, 1, 2, 3)
        t.attach(gtk.Label(_('Filepath:')), 0, 1, 3, 4)

        row_num = 4
        for key in metadata:
            if metadata[key] is not None:
                t.attach( gtk.Label(key.capitalize()+':'),
                          0, 1, row_num, row_num+1 )
                row_num += 1

        t.foreach(lambda x, y: x.set_alignment(1, 0.5), None)
        t.foreach(lambda x, y: x.set_markup('<b>%s</b>' % x.get_label()), None)

        t.attach(gtk.Label(playlist_item.title or _('<not modified>')),1,2,0,1)
        t.attach(gtk.Label(str(playlist_item)), 1, 2, 1, 2)
        t.attach(gtk.Label(playlist_item.playlist_id), 1, 2, 2, 3)
        t.attach(gtk.Label(playlist_item.filepath), 1, 2, 3, 4)

        row_num = 4
        for key in metadata:
            value = metadata[key]
            if key == 'length':
                value = util.convert_ns(value)
            if metadata[key] is not None:
                t.attach( gtk.Label( str(value) or _('<not set>')),
                          1, 2, row_num, row_num+1)
                row_num += 1

        t.foreach(lambda x, y: x.get_alignment() == (0.5, 0.5) and \
                               x.set_alignment(0, 0.5), None)

        t.set_border_width(8)
        t.set_row_spacings(4)
        t.set_col_spacings(8)

        l = gtk.ListStore(str, str)
        t = gtk.TreeView(l)
        cr = gtk.CellRendererText()
        cr.set_property('ellipsize', pango.ELLIPSIZE_END)
        c = gtk.TreeViewColumn(_('Title'), cr, text=0)
        c.set_expand(True)
        t.append_column(c)
        c = gtk.TreeViewColumn(_('Time'), gtk.CellRendererText(), text=1)
        t.append_column(c)
        playlist_item.load_bookmarks()
        for bookmark in playlist_item.bookmarks:
            l.append([bookmark.bookmark_name, \
                    util.convert_ns(bookmark.seek_position)])

        sw = gtk.ScrolledWindow()
        sw.set_shadow_type(gtk.SHADOW_IN)
        sw.add(t)
        sw.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        e = gtk.Expander(_('Bookmarks'))
        e.add(sw)
        if not platform.MAEMO:
            self.vbox.pack_start(e)
