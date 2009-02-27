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
# Based on http://thpinfo.com/2008/panucci/:
#  A resuming media player for Podcasts and Audiobooks
#  Copyright (c) 2008-05-26 Thomas Perl <thpinfo.com>
#  (based on http://pygstdocs.berlios.de/pygst-tutorial/seeking.html)
#


import logging
import sys
import os, os.path
import time

import gtk
import gobject

# At the moment, we don't have gettext support, so
# make a dummy "_" function to passthrough the string
_ = lambda s: s

log = logging.getLogger('panucci.panucci')

import util

try:
    import hildon
except:
    if util.platform == util.MAEMO:
        log.critical( 'Using GTK widgets, install "python2.5-hildon" '
            'for this to work properly.' )

from simplegconf import gconf
from settings import settings
from player import player
from dbusinterface import interface

about_name = 'Panucci'
about_text = _('Resuming audiobook and podcast player')
about_authors = ['Thomas Perl', 'Nick (nikosapi)', 'Matthew Taylor']
about_website = 'http://panucci.garage.maemo.org/'
app_version = ''
donate_wishlist_url = 'http://www.amazon.de/gp/registry/2PD2MYGHE6857'
donate_device_url = 'http://maemo.gpodder.org/donate.html'

short_seek = 10
long_seek = 60

coverart_names = [ 'cover', 'cover.jpg', 'cover.png' ]
coverart_size = [240, 240] if util.platform == util.MAEMO else [130, 130]
        
gtk.about_dialog_set_url_hook(util.open_link, None)
gtk.icon_size_register('panucci-button', 32, 32)

def image(widget, filename, is_stock=False):
    widget.remove(widget.get_child())
    image = None
    if is_stock:
        image = gtk.image_new_from_stock(
            filename, gtk.icon_size_from_name('panucci-button') )
    else:
        filename = util.find_image(filename)
        if filename is not None:
            image = gtk.image_new_from_file(filename)

    if image is not None:
        if util.platform == util.MAEMO:
            image.set_padding(20, 20)
        else:
            image.set_padding(5, 5)
        widget.add(image)
        image.show()

def dialog( toplevel_window, title, question, description ):
    """ Present the user with a yes/no/cancel dialog 
        Reponse: Yes = True, No = False, Cancel = None """

    dlg = gtk.MessageDialog( toplevel_window, gtk.DIALOG_MODAL,
        gtk.MESSAGE_QUESTION )
    dlg.set_title(title)
    dlg.add_button( gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL )
    dlg.add_button( gtk.STOCK_NO, gtk.RESPONSE_NO )
    dlg.add_button( gtk.STOCK_YES, gtk.RESPONSE_YES )
    dlg.set_markup( '<span weight="bold" size="larger">%s</span>\n\n%s' % (
        question, description ))

    response = dlg.run()
    dlg.destroy()

    if response == gtk.RESPONSE_YES:
        return True
    elif response == gtk.RESPONSE_NO:
        return False
    elif response in [gtk.RESPONSE_CANCEL, gtk.RESPONSE_DELETE_EVENT]:
        return None

def get_file_from_filechooser( toplevel_window, save_file=False, save_to=None):
    if util.platform == util.MAEMO:
        if save_file:
            args = ( toplevel_window, gtk.FILE_CHOOSER_ACTION_SAVE )
        else:
            args = ( toplevel_window, gtk.FILE_CHOOSER_ACTION_OPEN )

        dlg = hildon.FileChooserDialog( *args )
    else:
        if save_file:
            args = ( _('Select file to save playlist to'), None,
                gtk.FILE_CHOOSER_ACTION_SAVE,
                (( gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT,
                gtk.STOCK_SAVE, gtk.RESPONSE_OK )) )
        else:
            args = ( _('Select podcast or audiobook'), None,
                gtk.FILE_CHOOSER_ACTION_OPEN,
                (( gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT,
                gtk.STOCK_MEDIA_PLAY, gtk.RESPONSE_OK )) )

        dlg = gtk.FileChooserDialog(*args)

    current_folder = os.path.expanduser(settings.last_folder)

    if current_folder is not None and os.path.isdir(current_folder):
        dlg.set_current_folder(current_folder)

    if save_file and save_to is not None:
        dlg.set_current_name(save_to)

    if dlg.run() == gtk.RESPONSE_OK:
        filename = dlg.get_filename()
        settings.last_folder = dlg.get_current_folder()
    else:
        filename = None

    dlg.destroy()
    return filename

class BookmarksWindow(gtk.Window):
    def __init__(self):
        gtk.Window.__init__(self, gtk.WINDOW_TOPLEVEL)
        self.__log = logging.getLogger('panucci.panucci.BookmarksWindow')

        self.set_title('Bookmarks')
        window_icon = util.find_image('panucci.png')
        if window_icon is not None:
            self.set_icon_from_file( window_icon )

        self.set_default_size(400, 300)
        self.set_border_width(10)
        self.vbox = gtk.VBox()
        self.vbox.set_spacing(5)
        self.treeview = gtk.TreeView()
        self.treeview.set_enable_tree_lines(True)
        self.treeview.set_headers_visible(True)
        self.update_model()

        ncol = gtk.TreeViewColumn(_('Name'))
        ncell = gtk.CellRendererText()
        ncell.set_property('editable', True)
        ncell.connect('edited', self.label_edited)
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
        self.vbox.add(sw)
        self.hbox = gtk.HButtonBox()
        self.add_button = gtk.Button(gtk.STOCK_ADD)
        self.add_button.set_use_stock(True)
        self.add_button.connect('clicked', self.add_bookmark)
        self.hbox.pack_start(self.add_button)
        self.remove_button = gtk.Button(gtk.STOCK_REMOVE)
        self.remove_button.set_use_stock(True)
        self.remove_button.connect('clicked', self.remove_bookmark)
        self.hbox.pack_start(self.remove_button)
        self.jump_button = gtk.Button(gtk.STOCK_JUMP_TO)
        self.jump_button.set_use_stock(True)
        self.jump_button.connect('clicked', self.jump_bookmark)
        self.hbox.pack_start(self.jump_button)
        self.close_button = gtk.Button(gtk.STOCK_CLOSE)
        self.close_button.set_use_stock(True)
        self.close_button.connect('clicked', self.close)
        self.hbox.pack_start(self.close_button)
        self.vbox.pack_start(self.hbox, False, True)
        self.add(self.vbox)
        self.show_all()

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
                player.playlist.move_item( from_row, to_row )

        else:
            self.__log.debug('No drop_data or selection.data available')

    def update_model(self):
        self.model = player.playlist.get_bookmark_model()
        self.treeview.set_model(self.model)

    def close(self, w):
        player.playlist.update_bookmarks()
        self.destroy()

    def label_edited(self, cellrenderer, path, new_text):
        iter = self.model.get_iter(path)
        old_text = self.model.get_value(iter, 1)

        if new_text.strip():
            if old_text != new_text:
                self.model.set_value(iter, 1, new_text)
                m, bkmk_id, biter, item_id, iiter = self.__cur_selection()

                player.playlist.update_bookmark(
                    item_id, bkmk_id, name=new_text )
        else:
            self.model.set_value(iter, 1, old_text)

    def add_bookmark(self, w=None, lbl=None, pos=None):
        (label, position) = player.get_formatted_position(pos)
        label = label if lbl is None else lbl
        position = position if pos is None else pos
        player.playlist.save_bookmark( label, position )
        self.update_model()

    def __cur_selection(self):
        bookmark_id, bookmark_iter, item_id, item_iter = (None,)*4

        selection = self.treeview.get_selection()
        # Assume the user selects a bookmark.
        #   bookmark_iter will get set to None if that is not the case...
        model, bookmark_iter = selection.get_selected()

        if bookmark_iter is not None:
            item_iter = model.iter_parent(bookmark_iter)

            # bookmark_iter is actually an item_iter
            if item_iter is None:
                item_iter = bookmark_iter
                item_id = model.get_value(item_iter, 0)
                bookmark_id, bookmark_iter = None, None
            else:
                bookmark_id = model.get_value(bookmark_iter, 0)
                item_id = model.get_value(item_iter, 0)

        return model, bookmark_id, bookmark_iter, item_id, item_iter

    def remove_bookmark(self, w):
        model, bkmk_id, bkmk_iter, item_id, item_iter = self.__cur_selection()
        player.playlist.remove_bookmark( item_id, bkmk_id )
        if bkmk_iter is not None:
            model.remove(bkmk_iter)
        elif item_iter is not None:
            model.remove(item_iter)

    def jump_bookmark(self, w):
        model, bkmk_id, bkmk_iter, item_id, item_iter = self.__cur_selection()
        if item_iter is not None:
            player.stop()
            player.playlist.load_from_bookmark_id( item_id, bkmk_id )
            player.play()

class GTK_Main(object):

    def __init__(self, filename=None):
        self.__log = logging.getLogger('panucci.panucci.GTK_Main')
        interface.register_gui(self)
        self.pickle_file_conversion()

        self.recent_files = []
        self.progress_timer_id = None
        self.volume_timer_id = None
        self.make_main_window()
        self.has_coverart = False
        self.set_volume(settings.volume)

        if util.platform==util.MAEMO and interface.headset_device is not None:
            # Enable play/pause with headset button
            interface.headset_device.connect_to_signal(
                'Condition', self.handle_headset_button )

        player.register( 'stopped', self.on_player_stopped )
        player.register( 'playing', self.on_player_playing )
        player.register( 'paused', self.on_player_paused )
        player.register( 'end_of_playlist', self.on_player_end_of_playlist )
        player.playlist.register( 'new_track', self.on_player_new_track )
        player.playlist.register( 'file_queued', self.on_file_queued )
        player.init()

    def make_main_window(self):
        import pango

        if util.platform == util.MAEMO:
            self.app = hildon.Program()
            window = hildon.Window()
            self.app.add_window(window)
        else:
            window = gtk.Window(gtk.WINDOW_TOPLEVEL)

        window.set_title('Panucci')
        self.window_icon = util.find_image('panucci.png')
        if self.window_icon is not None:
            window.set_icon_from_file( self.window_icon )
        window.set_default_size(400, -1)
        window.set_border_width(0)
        window.connect("destroy", self.destroy)
        self.main_window = window

        if util.platform == util.MAEMO:
            window.set_menu(self.create_menu())
        else:
            menu_vbox = gtk.VBox()
            menu_vbox.set_spacing(0)
            window.add(menu_vbox)
            menu_bar = gtk.MenuBar()
            root_menu = gtk.MenuItem('Panucci')
            root_menu.set_submenu(self.create_menu())
            menu_bar.append(root_menu)
            menu_vbox.pack_start(menu_bar, False, False, 0)
            menu_bar.show()

        main_hbox = gtk.HBox()
        main_hbox.set_spacing(6)
        if util.platform == util.MAEMO:
            window.add(main_hbox)
        else:
            menu_vbox.pack_end(main_hbox, True, True, 6)

        main_vbox = gtk.VBox()
        main_vbox.set_spacing(6)
        # add a vbox to the main_hbox
        main_hbox.pack_start(main_vbox, True, True)

        # a hbox to hold the cover art and metadata vbox
        metadata_hbox = gtk.HBox()
        metadata_hbox.set_spacing(6)
        main_vbox.pack_start(metadata_hbox, True, False)

        self.cover_art = gtk.Image()
        metadata_hbox.pack_start( self.cover_art, False, False )

        # vbox to hold metadata
        metadata_vbox = gtk.VBox()
        metadata_vbox.set_spacing(8)
        empty_label = gtk.Label()
        metadata_vbox.pack_start(empty_label, True, True)
        self.artist_label = gtk.Label('')
        self.artist_label.set_ellipsize(pango.ELLIPSIZE_END)
        metadata_vbox.pack_start(self.artist_label, False, False)
        self.album_label = gtk.Label('')
        self.album_label.set_ellipsize(pango.ELLIPSIZE_END)
        metadata_vbox.pack_start(self.album_label, False, False)
        self.title_label = gtk.Label('')
        self.title_label.set_line_wrap(True)
        metadata_vbox.pack_start(self.title_label, False, False)
        empty_label = gtk.Label()
        metadata_vbox.pack_start(empty_label, True, True)
        metadata_hbox.pack_start( metadata_vbox, True, True )

        progress_eventbox = gtk.EventBox()
        progress_eventbox.set_events(gtk.gdk.BUTTON_PRESS_MASK)
        progress_eventbox.connect('button-press-event', self.on_progressbar_changed)
        self.progress = gtk.ProgressBar()
        # make the progress bar more "finger-friendly"
        if util.platform == util.MAEMO:
            self.progress.set_size_request( -1, 50 )
        progress_eventbox.add(self.progress)
        main_vbox.pack_start( progress_eventbox, False, False )

        # make the button box
        buttonbox = gtk.HBox()
        self.rrewind_button = gtk.Button('')
        image(self.rrewind_button, 'media-skip-backward.png')
        self.rrewind_button.connect('clicked', self.seekbutton_callback, -1*long_seek)
        buttonbox.add(self.rrewind_button)
        self.rewind_button = gtk.Button('')
        image(self.rewind_button, 'media-seek-backward.png')
        self.rewind_button.connect('clicked', self.seekbutton_callback, -1*short_seek)
        buttonbox.add(self.rewind_button)
        self.play_pause_button = gtk.Button('')
        image(self.play_pause_button, gtk.STOCK_OPEN, True)
        self.button_handler_id = self.play_pause_button.connect( 
            'clicked', self.open_file_callback )
        buttonbox.add(self.play_pause_button)
        self.forward_button = gtk.Button('')
        image(self.forward_button, 'media-seek-forward.png')
        self.forward_button.connect('clicked', self.seekbutton_callback, short_seek)
        buttonbox.add(self.forward_button)
        self.fforward_button = gtk.Button('')
        image(self.fforward_button, 'media-skip-forward.png')
        self.fforward_button.connect('clicked', self.seekbutton_callback, long_seek)
        buttonbox.add(self.fforward_button)
        self.bookmarks_button = gtk.Button('')
        image(self.bookmarks_button, 'bookmark-new.png')
        self.bookmarks_button.connect('clicked', self.bookmarks_callback)
        buttonbox.add(self.bookmarks_button)
        self.set_controls_sensitivity(False)
        main_vbox.pack_start(buttonbox, False, False)

        window.show_all()

        if util.platform == util.MAEMO:
            self.volume = hildon.VVolumebar()
            self.volume.set_property('can-focus', False)
            self.volume.connect('level_changed', self.volume_changed_hildon)
            self.volume.connect('mute_toggled', self.mute_toggled)
            window.connect('key-press-event', self.on_key_press)
            main_hbox.pack_start(self.volume, False, True)

            # Add a button to pop out the volume bar
            self.volume_button = gtk.ToggleButton('')
            image(self.volume_button, 'media-speaker.png')
            self.volume_button.connect('clicked', self.toggle_volumebar)
            self.volume.connect(
                'show', lambda x: self.volume_button.set_active(True))
            self.volume.connect(
                'hide', lambda x: self.volume_button.set_active(False))
            buttonbox.add(self.volume_button)
            self.volume_button.show()

            # Disable focus for all widgets, so we can use the cursor
            # keys + enter to directly control our media player, which
            # is handled by "key-press-event"
            for w in (
                    self.rrewind_button, self.rewind_button,
                    self.play_pause_button, self.forward_button,
                    self.fforward_button, self.progress, 
                    self.bookmarks_button, self.volume_button, ):
                w.unset_flags(gtk.CAN_FOCUS)
        else:
            self.volume = gtk.VolumeButton()
            self.volume.connect('value-changed', self.volume_changed_gtk)
            buttonbox.add(self.volume)
            self.volume.show()

    def create_menu(self):
        # the main menu
        menu = gtk.Menu()

        menu_open = gtk.ImageMenuItem(gtk.STOCK_OPEN)
        menu_open.connect("activate", self.open_file_callback)
        menu.append(menu_open)

        menu_queue = gtk.MenuItem(_('Add file to the queue'))
        menu_queue.connect('activate', self.queue_file_callback)
        menu.append(menu_queue)

        # the recent files menu
        self.menu_recent = gtk.MenuItem(_('Recent Files'))
        menu.append(self.menu_recent)
        self.create_recent_files_menu()

        menu.append(gtk.SeparatorMenuItem())

        menu_bookmarks = gtk.MenuItem(_('Bookmarks'))
        menu_bookmarks.connect('activate', self.bookmarks_callback)
        menu.append(menu_bookmarks)

        
        # the settings sub-menu
        menu_settings = gtk.MenuItem(_('Settings'))
        menu.append(menu_settings)

        menu_settings_sub = gtk.Menu()
        menu_settings.set_submenu(menu_settings_sub)

        menu_settings_lock_progress = gtk.CheckMenuItem(_('Lock Progress Bar'))
        menu_settings_lock_progress.connect('toggled', lambda w: 
            setattr( settings, 'progress_locked', w.get_active()))
        menu_settings_lock_progress.set_active(self.lock_progress)
        menu_settings_sub.append(menu_settings_lock_progress)

        menu.append(gtk.SeparatorMenuItem())

        # the donate sub-menu
        menu_donate = gtk.MenuItem(_('Donate'))
        menu.append(menu_donate)

        menu_donate_sub = gtk.Menu()
        menu_donate.set_submenu(menu_donate_sub)

        menu_donate_device = gtk.MenuItem(_('Developer device'))
        menu_donate_device.connect("activate", lambda w: webbrowser.open_new(donate_device_url))
        menu_donate_sub.append(menu_donate_device)

        menu_donate_wishlist = gtk.MenuItem(_('Amazon Wishlist'))
        menu_donate_wishlist.connect("activate", lambda w: webbrowser.open_new(donate_wishlist_url))
        menu_donate_sub.append(menu_donate_wishlist)

        menu_about = gtk.ImageMenuItem(gtk.STOCK_ABOUT)
        menu_about.connect("activate", self.show_about, self.main_window)
        menu.append(menu_about)

        menu.append(gtk.SeparatorMenuItem())

        menu_quit = gtk.ImageMenuItem(gtk.STOCK_QUIT)
        menu_quit.connect("activate", self.destroy)
        menu.append(menu_quit)

        return menu

    def create_recent_files_menu( self ):
        max_files = settings.max_recent_files
        self.recent_files = player.playlist.get_recent_files(max_files)
        menu_recent_sub = gtk.Menu()

        temp_playlist = os.path.expanduser(settings.temp_playlist)

        if len(self.recent_files) > 0:
            for f in self.recent_files:
                # don't include the temporary playlist in the file list
                if f == temp_playlist: continue
                filename, extension = os.path.splitext(os.path.basename(f))
                menu_item = gtk.MenuItem( filename.replace('_', ' '))
                menu_item.connect('activate', self.on_recent_file_activate, f)
                menu_recent_sub.append(menu_item)
        else:
            menu_item = gtk.MenuItem(_('No recent files available.'))
            menu_item.set_sensitive(False)
            menu_recent_sub.append(menu_item)

        self.menu_recent.set_submenu(menu_recent_sub)

    def on_recent_file_activate(self, widget, filepath):
        self.play_file(filepath)

    @property
    def lock_progress(self):
        return settings.progress_locked

    def show_about(self, w, win):
        dialog = gtk.AboutDialog()
        dialog.set_website(about_website)
        dialog.set_website_label(about_website)
        dialog.set_name(about_name)
        dialog.set_authors(about_authors)
        dialog.set_comments(about_text)
        dialog.set_version(app_version)
        dialog.run()
        dialog.destroy()

    def destroy(self, widget):
        player.quit()
        gtk.main_quit()

    def handle_headset_button(self, event, button):
        if event == 'ButtonPressed' and button == 'phone':
            self.on_btn_play_pause_clicked()

    def queue_file_callback(self, widget=None):
        filename = get_file_from_filechooser(self.main_window)
        if filename is not None:
            self.queue_file(filename)

    def check_queue(self):
        """ Makes sure the queue is saved if it has been modified
                True means a new file can be opened
                False means the user does not want to continue """

        if player.playlist.queue_modified:
            response = dialog(
                self.main_window, _('Save queue to playlist file'),
                _('Save Queue?'), _("The queue has been modified, "
                "you will lose all additions if you don't save.") )

            self.__log.debug('Response to "Save Queue?": %s', response)

            if response is None:
                return False
            elif response:
                return self.save_to_playlist_callback()
            elif not response:
                return True
            else:
                return False
        else:
            return True

    def open_file_callback(self, widget=None):
        if self.check_queue():
            filename = get_file_from_filechooser(self.main_window)
            if filename is not None:
                self._play_file(filename)

    def save_to_playlist_callback(self, widget=None):
        filename = get_file_from_filechooser(
            self.main_window, save_file=True, save_to='playlist.m3u' )

        if filename is None:
            return False

        if os.path.isfile(filename):
            response = dialog(
                self.main_window, _('Overwrite File Warning'),
                _('Overwrite ') + '%s?' % os.path.basename(filename),
                _('All data in the file will be erased.') )

            if response is None:
                return None
            elif response:
                pass
            elif not response:
                return self.save_to_playlist_callback()

        ext = util.detect_filetype(filename)
        if not player.playlist.save_to_new_playlist(filename, ext):
            util.notify(_('Error saving playlist...'))
            return False

        return True

    def set_controls_sensitivity(self, sensitive):
        self.forward_button.set_sensitive(sensitive)
        self.rewind_button.set_sensitive(sensitive)
        self.fforward_button.set_sensitive(sensitive)
        self.rrewind_button.set_sensitive(sensitive)

    def on_key_press(self, widget, event):
        if event.keyval == gtk.keysyms.F7: #plus
            self.set_volume( min( 1, self.get_volume() + 0.10 ))
        elif event.keyval == gtk.keysyms.F8: #minus
            self.set_volume( max( 0, self.get_volume() - 0.10 ))
        elif event.keyval == gtk.keysyms.Left: # seek back
            self.rewind_callback(self.rewind_button)
        elif event.keyval == gtk.keysyms.Right: # seek forward
            self.forward_callback(self.forward_button)
        elif event.keyval == gtk.keysyms.Return: # play/pause
            self.on_btn_play_pause_clicked()

    # The following two functions get and set the
    #   volume from the volume control widgets.
    def get_volume(self):
        if util.platform == util.MAEMO:
            return self.volume.get_level()/100.0
        else:
            return self.volume.get_value()

    def set_volume(self, vol):
        """ vol is a float from 0 to 1 """
        assert 0 <= vol <= 1
        if util.platform == util.MAEMO:
            self.volume.set_level(vol*100.0)
        else:
            self.volume.set_value(vol)

    def __set_volume_hide_timer(self, timeout, force_show=False):
        if force_show or self.volume_button.get_active():
            self.volume.show()
            if self.volume_timer_id is not None:
                gobject.source_remove(self.volume_timer_id)

            self.volume_timer_id = gobject.timeout_add(
                1000 * timeout, self.__volume_hide_callback )

    def __volume_hide_callback(self):
        self.volume_timer_id = None
        self.volume.hide()
        return False

    def toggle_volumebar(self, widget=None):
        if self.volume_timer_id is None:
            self.__set_volume_hide_timer(5)
        else:
           self.__volume_hide_callback()

    def volume_changed_gtk(self, widget, new_value=0.5):
        player.volume_level = new_value

    def volume_changed_hildon(self, widget):
        self.__set_volume_hide_timer( 4, force_show=True )
        player.volume_level = widget.get_level()/100.0

    def mute_toggled(self, widget):
        if widget.get_mute():
            player.volume_level = 0
        else:
            player.volume_level = widget.get_level()/100.0

    def show_main_window(self):
        self.main_window.present()

    def play_file(self, filename):
        if self.check_queue():
            self._play_file(filename)

    def _play_file(self, filename, pause_on_load=False):
        player.stop()

        player.playlist.load( os.path.abspath(filename) )
        if player.playlist.is_empty:
            return False

        player.play()

    def on_player_stopped(self):
        self.stop_progress_timer()
        self.title_label.set_size_request(-1,-1)
        self.reset_progress()
        self.set_controls_sensitivity(False)

    def on_player_playing(self):
        self.start_progress_timer()
        image(self.play_pause_button, 'media-playback-pause.png')

    def on_player_new_track(self, metadata):
        image(self.play_pause_button, 'media-playback-start.png')
        self.play_pause_button.disconnect(self.button_handler_id)
        self.button_handler_id = self.play_pause_button.connect(
            'clicked', self.on_btn_play_pause_clicked )

        self.set_controls_sensitivity(True)
        for widget in [self.title_label,self.artist_label,self.album_label]:
            widget.set_text('')
            widget.hide()

        self.cover_art.hide()
        self.has_coverart = False
        self.set_metadata(metadata)

        text, position = player.get_formatted_position()
        estimated_length = metadata['length']
        self.set_progress_callback( position, estimated_length )

    def on_player_paused(self):
        self.stop_progress_timer() # This should save some power
        image(self.play_pause_button, 'media-playback-start.png')

    def on_player_end_of_playlist(self):
        self.play_pause_button.disconnect(self.button_handler_id)
        self.button_handler_id = self.play_pause_button.connect(
            'clicked', self.open_file_callback )
        image(self.play_pause_button, gtk.STOCK_OPEN, True)

    def on_file_queued(self, filepath, success):
        filename = os.path.basename(filepath)
        if success:
            self.__log.info(util.notify('%s added successfully.' % filename ))
        else:
            self.__log.error(
                util.notify('Error adding %s to the queue.' % filename) )

    def reset_progress(self):
        self.progress.set_fraction(0)
        self.set_progress_callback(0,0)

    def set_progress_callback(self, time_elapsed, total_time):
        """ times must be in nanoseconds """
        time_string = "%s / %s" % ( util.convert_ns(time_elapsed),
            util.convert_ns(total_time) )
        self.progress.set_text( time_string )
        fraction = float(time_elapsed) / float(total_time) if total_time else 0
        self.progress.set_fraction( fraction )

    def on_progressbar_changed(self, widget, event):
        if ( not self.lock_progress and
                event.type == gtk.gdk.BUTTON_PRESS and event.button == 1 ):
            new_fraction = event.x/float(widget.get_allocation().width)
            player.do_seek(percent=new_fraction)

    def on_btn_play_pause_clicked(self, widget=None):
        player.play_pause_toggle()

    def progress_timer_callback( self ):
        if player.playing and not player.seeking:
            pos_int, dur_int = player.get_position_duration()
            # This prevents bogus values from being set while seeking
            if ( pos_int > 10**9 ) and ( dur_int > 10**9 ):
                self.set_progress_callback( pos_int, dur_int )
        return True

    def start_progress_timer( self ):
        if self.progress_timer_id is not None:
            self.stop_progress_timer()

        self.progress_timer_id = gobject.timeout_add(
            1000, self.progress_timer_callback )

    def stop_progress_timer( self ):
        if self.progress_timer_id is not None:
            gobject.source_remove( self.progress_timer_id )
            self.progress_timer_id = None

    def set_coverart( self, pixbuf ):
        self.cover_art.set_from_pixbuf(pixbuf)
        self.cover_art.show()
        self.has_coverart = True

    def set_metadata( self, tag_message ):
        tags = { 'title': self.title_label, 'artist': self.artist_label,
                 'album': self.album_label }

        if tag_message.has_key('image') and tag_message['image'] is not None:
            value = tag_message['image']

            pbl = gtk.gdk.PixbufLoader()
            try:
                pbl.write(value)
                pbl.close()
                pixbuf = pbl.get_pixbuf().scale_simple(
                  coverart_size[0], coverart_size[1], gtk.gdk.INTERP_BILINEAR )
                self.set_coverart(pixbuf)
            except Exception, e:
                self.__log.exception('Error setting coverart...')

        tag_vals = dict([ (i,'') for i in tags.keys()])
        for tag,value in tag_message.iteritems():
            if tags.has_key(tag) and value is not None and value.strip():
                tags[tag].set_markup('<big>'+value+'</big>')
                tag_vals[tag] = value
                tags[tag].set_alignment( 0.5*int(not self.has_coverart), 0.5)
                tags[tag].show()
            if tag == 'title':
                if util.platform == util.MAEMO:
                    self.main_window.set_title(value)
                    # oh man this is hacky :(
                    if self.has_coverart:
                        tags[tag].set_size_request(420,-1)
                        if len(value) >= 80: value = value[:80] + '...'
                else:
                    self.main_window.set_title('Panucci - ' + value)

                tags[tag].set_markup('<b><big>'+value+'</big></b>')

    def seekbutton_callback( self, widget, seek_amount ):
        resp = player.do_seek(from_current=seek_amount*10**9)
        if resp:
            # Preemptively update the progressbar to make seeking smoother
            self.set_progress_callback( *resp )

    def bookmarks_callback(self, w):
        BookmarksWindow()

    def pickle_file_conversion(self):
        pickle_file = os.path.expanduser('~/.rmp-bookmarks')
        if os.path.isfile(pickle_file):
            import pickle_converter

            self.__log.info(
                util.notify( _('Converting old pickle format to SQLite.') ))
            self.__log.info( util.notify( _('This may take a while...') ))

            if pickle_converter.load_pickle_file(pickle_file):
                self.__log.info(
                    util.notify( _('Pickle file converted successfully.') ))
            else:
                self.__log.error( util.notify(
                    _('Error converting pickle file, check your log...') ))

def run(filename=None):
    GTK_Main( filename )
    gtk.main()

if __name__ == '__main__':
    log.error( 'WARNING: Use the "panucci" executable to run this program.' )
    log.error( 'Exiting...' )
    sys.exit(1)

