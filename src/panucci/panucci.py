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


import sys
import os, os.path
import time
import cPickle as pickle

import gtk
import gobject
import pygst
pygst.require('0.10')
import gst

import dbus
import dbus.service
import dbus.mainloop
import dbus.glib

# At the moment, we don't have gettext support, so
# make a dummy "_" function to passthrough the string
_ = lambda s: s

import util
running_on_tablet = util.platform == util.MAEMO

try:
    import hildon
except:
    if running_on_tablet:
        log('Using GTK widgets, install "python2.5-hildon" for this to work properly.')

from util import log
from simplegconf import gconf
from playlist import Playlist

about_name = 'Panucci'
about_text = _('Resuming audiobook and podcast player')
about_authors = ['Thomas Perl', 'Nick (nikosapi)', 'Matthew Taylor']
about_website = 'http://panucci.garage.maemo.org/'
donate_wishlist_url = 'http://www.amazon.de/gp/registry/2PD2MYGHE6857'
donate_device_url = 'http://maemo.gpodder.org/donate.html'

short_seek = 10
long_seek = 60

coverart_names = [ 'cover', 'cover.jpg', 'cover.png' ]
coverart_size = [240, 240] if running_on_tablet else [130, 130]
        
gtk.about_dialog_set_url_hook(util.open_link, None)
gtk.icon_size_register('panucci-button', 32, 32)

def image(widget, filename, is_stock=False):
    widget.remove(widget.get_child())
    image = None
    if is_stock:
        image = gtk.image_new_from_stock(filename, gtk.icon_size_from_name('panucci-button'))
    else:
        filename = util.find_image(filename)
        if filename is not None:
            image = gtk.image_new_from_file(filename)

    if image is not None:
        if running_on_tablet:
            image.set_padding(20, 20)
        else:
            image.set_padding(5, 5)
        widget.add(image)
        image.show()

class BookmarksWindow(gtk.Window):
    def __init__(self, main):
        self.main = main
        gtk.Window.__init__(self, gtk.WINDOW_TOPLEVEL)
        self.set_title('Bookmarks')
        self.set_modal(True)
        self.set_default_size(400, 300)
        self.set_border_width(10)
        self.vbox = gtk.VBox()
        self.vbox.set_spacing(5)
        self.treeview = gtk.TreeView()
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

    def update_model(self):
        self.model = self.main.playlist.get_bookmark_model()
        self.treeview.set_model(self.model)

    def close(self, w):
        self.destroy()

    def label_edited(self, cellrenderer, path, new_text):
        iter = self.model.get_iter(path)
        bkmk_id  = self.model.get_value(iter, 0)
        old_text = self.model.get_value(iter, 1)

        if new_text.strip():
            if old_text != new_text:
                self.model.set_value(iter, 1, new_text)
                self.main.playlist.update_bookmark( bkmk_id, name=new_text )
        else:
            self.model.set_value(iter, 1, old_text)

    def add_bookmark(self, w=None, lbl=None, pos=None):
        (label, position) = self.main.get_position(pos)
        label = label if lbl is None else lbl
        position = position if pos is None else pos
        self.main.playlist.save_bookmark( label, position )
        self.update_model()

    def remove_bookmark(self, w):
        selection = self.treeview.get_selection()
        (model, iter) = selection.get_selected()
        if iter is not None:
            bookmark_id = model.get_value(iter, 0)
            self.main.playlist.remove_bookmark( bookmark_id )
            model.remove(iter)

    def jump_bookmark(self, w):
        selection = self.treeview.get_selection()
        (model, iter) = selection.get_selected()
        if iter is not None:
            bookmark_id = model.get_value(iter, 0)
            self.main.stop_playing()
            self.main.playlist.load_from_bookmark( bookmark_id )
            self.main.start_playback()

class GTK_Main(dbus.service.Object):

    def __init__(self, bus_name, filename=None):
        dbus.service.Object.__init__(self, object_path="/player",
            bus_name=bus_name)

        self.gconf = gconf
        self.gconf.snotify(self.gconf_key_changed)

        self.playlist = Playlist()
        self.recent_files = []
        self.progress_timer_id = None
        self.volume_timer_id = None
        self.make_main_window()
        self.playing = False
        self.has_coverart = False

        if running_on_tablet:
            # Enable play/pause with headset button
            system_bus = dbus.SystemBus()
            headset_button = system_bus.get_object('org.freedesktop.Hal',
                '/org/freedesktop/Hal/devices/platform_retu_headset_logicaldev_input')
            headset_device = dbus.Interface(headset_button, 'org.freedesktop.Hal.Device')
            headset_device.connect_to_signal('Condition', self.handle_headset_button)

        self.want_to_seek = False
        self.player = None

        # Placeholder functions, these are generated dynamically
        self.get_volume_level = lambda: 0
        self.set_volume_level = lambda x: 0

        self.set_volume(self.gconf.sget('volume', float, 0.3))
        self.time_format = gst.Format(gst.FORMAT_TIME)

        if filename is None:
            if self.recent_files:
                self._play_file(self.recent_files[0], pause_on_load=True)
        else:
            self._play_file(filename)

    def make_main_window(self):
        import pango

        if running_on_tablet:
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

        if running_on_tablet:
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
        if running_on_tablet:
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
        if running_on_tablet: # make the progress bar more "finger-friendly"
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
        self.button = gtk.Button('')
        image(self.button, gtk.STOCK_OPEN, True)
        self.button_handler_id = self.button.connect( 
            'clicked', self.open_file_callback )
        buttonbox.add(self.button)
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

        if running_on_tablet:
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
            self.volume.connect('show', lambda x: self.volume_button.set_active(True))
            self.volume.connect('hide', lambda x: self.volume_button.set_active(False))
            buttonbox.add(self.volume_button)
            self.volume_button.show()

            # Disable focus for all widgets, so we can use the cursor
            # keys + enter to directly control our media player, which
            # is handled by "key-press-event"
            for w in (self.rrewind_button, self.rewind_button, self.button,
                    self.forward_button, self.fforward_button, self.bookmarks_button,
                    self.volume_button, self.progress):
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
            self.gconf.sset('progress_locked', w.get_active()))
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
        max_files = self.gconf.sget('max_recent_files', int, 10)
        self.recent_files = self.playlist.get_recent_files(max_files)
        menu_recent_sub = gtk.Menu()

        temp_playlist = gconf.sget('temp_playlist', str, '~/.panucci.m3u')
        temp_playlist = os.path.expanduser(temp_playlist)

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
        return self.gconf.sget('progress_locked', bool, False)

    def show_about(self, w, win):
        dialog = gtk.AboutDialog()
        dialog.set_website(about_website)
        dialog.set_website_label(about_website)
        dialog.set_name(about_name)
        dialog.set_authors(about_authors)
        dialog.set_comments(about_text)
        dialog.run()
        dialog.destroy()

    def get_position(self, pos=None):
        if pos is None:
            if self.playing:
                (pos, dur) = self.player_get_position()
            else:
                pos = self.playlist.get_current_position()
        text = util.convert_ns(pos)
        return (text, pos)

    def destroy(self, widget):
        if self.playlist.queue_modified:
            log('Queue modified, saving temporary playlist')
            self.playlist.save_temp_playlist()

        self.stop_playing()
        self.gconf.sset( 'volume', self.get_volume() )
        gtk.main_quit()

    def gconf_key_changed(self, client, connection_id, entry, args):
        log( 'gconf key %s changed: %s' % (entry.get_key(), entry.get_value()))

    def handle_headset_button(self, event, button):
        if event == 'ButtonPressed' and button == 'phone':
            self.on_btn_play_pause_clicked(self.button)

    def get_file_from_filechooser(self, save_file=False, save_to=None):
        if running_on_tablet:
            if save_file:
                args = ( self.main_window, gtk.FILE_CHOOSER_ACTION_SAVE )
            else:
                args = ( self.main_window, gtk.FILE_CHOOSER_ACTION_OPEN )

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

        current_folder = self.gconf.sget('last_folder', str,
            os.path.expanduser('~') )

        if current_folder is not None and os.path.isdir(current_folder):
            dlg.set_current_folder(current_folder)

        if save_file and save_to is not None:
            dlg.set_current_name(save_to)

        if dlg.run() == gtk.RESPONSE_OK:
            filename = dlg.get_filename()
            self.gconf.sset('last_folder', dlg.get_current_folder())
        else:
            filename = None

        dlg.destroy()
        return filename

    def queue_file_callback(self, widget=None):
        filename = self.get_file_from_filechooser()
        if filename is not None:
            self.queue_file(filename)

    def check_queue(self):
        """ Makes sure the queue is saved if it has been modified
                True means a new file can be opened
                False means the user does not want to continue """

        if self.playlist.queue_modified:
            dlg = gtk.MessageDialog( self.main_window, gtk.DIALOG_MODAL,
                gtk.MESSAGE_QUESTION )
            dlg.set_title(_('Save queue to playlist file'))
            dlg.add_button( gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL )
            dlg.add_button( gtk.STOCK_NO, gtk.RESPONSE_NO )
            dlg.add_button( gtk.STOCK_YES, gtk.RESPONSE_YES )
            dlg.set_markup('<span weight="bold" size="larger">' +
                _('Save Queue?') + '</span>\n\n' +
                _('The queue has been modified, you will lose all additions if you don\'t save.'))

            response = dlg.run()
            dlg.destroy()

            if response == gtk.RESPONSE_YES:
                return self.save_to_playlist_callback()
            elif response == gtk.RESPONSE_NO:
                return True
            elif response in [gtk.RESPONSE_CANCEL, gtk.RESPONSE_DELETE_EVENT]:
                pass
        else:
            return True

        return False

    def open_file_callback(self, widget=None):
        if self.check_queue():
            filename = self.get_file_from_filechooser()
            if filename is not None:
                self._play_file(filename)

    def save_to_playlist_callback(self, widget=None):
        filename = self.get_file_from_filechooser(
            save_file=True, save_to='playlist.m3u' )

        if filename is None:
            return False

        ext = util.detect_filetype(filename)
        if not self.playlist.save_to_new_playlist(filename, ext):
            util.send_notification(_('Error saving playlist...'))
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
            self.on_btn_play_pause_clicked(self.button)

    # The following two functions get and set the volume from the volume control widgets
    def get_volume(self):
        if running_on_tablet:
            return self.volume.get_level()/100.0
        else:
            return self.volume.get_value()

    def set_volume(self, vol):
        """ vol is a float from 0 to 1 """
        assert 0 <= vol <= 1
        if running_on_tablet:
            self.volume.set_level(vol*100.0)
        else:
            self.volume.set_value(vol)

    def __set_volume_hide_timer(self, timeout, force_show=False):
        if force_show or self.volume_button.get_active():
            self.volume.show()
            if self.volume_timer_id is not None:
                gobject.source_remove(self.volume_timer_id)
            self.volume_timer_id = gobject.timeout_add(1000*timeout, self.__volume_hide_callback)

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
        self.set_volume_level( new_value )

    def volume_changed_hildon(self, widget):
        self.__set_volume_hide_timer( 4, force_show=True )
        self.set_volume_level( widget.get_level()/100.0 )

    def mute_toggled(self, widget):
        if widget.get_mute():
            self.set_volume_level( 0 )
        else:
            self.set_volume_level( widget.get_level()/100.0 )

    @dbus.service.method('org.panucci.interface')
    def show_main_window(self):
        self.main_window.present()

    @dbus.service.method('org.panucci.interface', in_signature='s')
    def queue_file(self, filepath):
        log('Attempting to queue file: %s' % filepath)
        filename = os.path.basename(filepath)
        if self.playlist.append( filepath ):
            util.send_notification('%s added successfully.' % filename )
        else:
            util.log('Error adding %s to the queue.' % filename, notify=True)

    @dbus.service.method('org.panucci.interface', in_signature='s')
    def play_file(self, filename):
        if self.check_queue():
            self._play_file(filename)

    def _play_file(self, filename, pause_on_load=False):
        self.stop_playing()

        self.playlist.load( os.path.abspath(filename) )
        if self.playlist.is_empty():
            return False

        self.start_playback(pause_on_load)

    @dbus.service.method('org.panucci.interface')
    def stop_playing(self):
        if self.playing:
            self.on_btn_play_pause_clicked(widget=None)

        self.button.disconnect(self.button_handler_id)
        self.button_handler_id = self.button.connect(
            'clicked', self.open_file_callback )

        if self.player is not None: 
            self.player.set_state(gst.STATE_NULL)

        self.stop_progress_timer()
        self.title_label.set_size_request(-1,-1)
        self.playing = False
        self.reset_progress()
        self.set_controls_sensitivity(False)
        image(self.button, gtk.STOCK_OPEN, True)

    def start_playback(self, pause_on_load=False):
        self.want_to_seek = True
        self.button.disconnect(self.button_handler_id)
        self.button_handler_id = self.button.connect(
            'clicked', self.on_btn_play_pause_clicked )

        self.set_controls_sensitivity(True)
        for widget in [ self.title_label, self.artist_label, self.album_label ]:
            widget.set_text('')
            widget.hide()
        self.cover_art.hide()
        self.set_metadata(self.playlist.get_file_metadata())
        self.setup_player()

        if pause_on_load:
            image(self.button, 'media-playback-start.png')
            self.set_controls_sensitivity(False)
            self.set_progress_callback( self.playlist.get_current_position(),
                self.playlist.get_estimated_duration() )
        else:
            self.on_btn_play_pause_clicked(widget=None)

    def setup_player(self):
        filetype = self.playlist.get_current_filetype()
        filepath = self.playlist.get_current_filepath()

        if None in [ filetype, filepath ]:
            return False

        if filetype.startswith('ogg') and running_on_tablet:
            log( 'Using OGG workaround, I hope this works...' )

            self.player = gst.Pipeline('player')
            source = gst.element_factory_make('gnomevfssrc', 'file-source')

            try:
                audio_decoder = gst.element_factory_make(
                    'tremor', 'vorbis-decoder' )
            except Exception, e:
                log( 'No ogg decoder available, install the "mogg" package.',
                    exception=e, title='Missing Decoder.', notify=True )
                return False

            self.__volume_control = gst.element_factory_make('volume', 'volume')
            audiosink = gst.element_factory_make('dsppcmsink', 'audio-output')

            self.player.add(source, audio_decoder, self.__volume_control, audiosink)
            gst.element_link_many(source, audio_decoder, self.__volume_control, audiosink)

            self.get_volume_level = lambda : self.__get_volume_level(self.__volume_control)
            self.set_volume_level = lambda x: self.__set_volume_level(x, self.__volume_control)

            source.set_property( 'location', 'file://' + filepath )
        else:
            log( 'Using plain-old playbin.' )

            self.player = gst.element_factory_make('playbin', 'player')

            # Workaround for volume on maemo, they use a 0 to 10 scale
            div = int(running_on_tablet)*10 or 1
            self.get_volume_level = lambda : self.__get_volume_level(self.player, div)
            self.set_volume_level = lambda x: self.__set_volume_level(x, self.player, div)

            self.player.set_property( 'uri', 'file://' + filepath )

        bus = self.player.get_bus()
        bus.add_signal_watch()
        bus.connect("message", self.on_message)

        self.set_volume_level(self.get_volume())

    def __get_volume_level(self, volume_control, divisor=1):
        vol = volume_control.get_property('volume') / float(divisor)
        assert 0 <= vol <= 1
        return vol

    def __set_volume_level(self, value, volume_control, multiplier=1):
        assert  0 <= value <= 1
        volume_control.set_property('volume', value * float(multiplier))

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
            self.do_seek(percent=new_fraction)

    def on_btn_play_pause_clicked(self, widget=None):
        self.playing = not self.playing

        if self.playing:
            self.start_progress_timer()
            self.playlist.play()
            self.player.set_state(gst.STATE_PLAYING)
            image(self.button, 'media-playback-pause.png')
        else:
            self.stop_progress_timer() # This should save some power
            pos, dur = self.player_get_position()
            self.playlist.pause(pos)
            self.player.set_state(gst.STATE_PAUSED)
            image(self.button, 'media-playback-start.png')

    def do_seek(self, from_beginning=None, from_current=None, percent=None ):
        """ Takes one of the following keyword arguments:
                from_beginning=n: seek n nanoseconds from the beinging of the file
                from_current=n: seek n nanoseconds from the current position
                percent=n: seek n percent from the beginning of the file
        """
        self.want_to_seek = True

        position, duration = self.player_get_position()
        # if position and duration are 0 then player_get_position caught an
        # exception. Therefore self.player isn't ready to be seeking.
        if not ( position or duration ) or self.player is None:
            return False

        if from_beginning is not None:
            assert from_beginning >= 0
            position = min( from_beginning, duration )
        elif from_current is not None:
            position = max( 0, min( position+from_current, duration ))
        elif percent is not None:
            assert 0 <= percent <= 1
            position = int(duration*percent)
        else:
            log('No seek parameters specified.')
            return False

        # Preemptively update the progressbar to make seeking nice and smooth
        self.set_progress_callback( position, duration )
        self.player.seek_simple(self.time_format, gst.SEEK_FLAG_FLUSH, position)
        self.want_to_seek = False

        return True

    def player_get_position(self):
        """ returns [ current position, total duration ] """
        try:
            pos_int = self.player.query_position(self.time_format, None)[0]
            dur_int = self.player.query_duration(self.time_format, None)[0]
        except:
            pos_int = dur_int = 0
        return pos_int, dur_int

    def progress_timer_callback( self ):
        if self.playing and not self.want_to_seek:
            pos_int, dur_int = self.player_get_position()
            # This prevents bogus values from being set while seeking
            if ( pos_int > 10**9 ) and ( dur_int > 10**9 ):
                self.set_progress_callback( pos_int, dur_int )
        return True

    def start_progress_timer( self ):
        if self.progress_timer_id is not None:
            self.stop_progress_timer()

        self.progress_timer_id = gobject.timeout_add( 1000, self.progress_timer_callback )

    def stop_progress_timer( self ):
        if self.progress_timer_id is not None:
            gobject.source_remove( self.progress_timer_id )
            self.progress_timer_id = None

    def on_message(self, bus, message):
        t = message.type

        if t == gst.MESSAGE_EOS:
            self.stop_playing()
            if self.playlist.next():
                self.start_playback()
            else:
                self.playlist.stop()

        elif t == gst.MESSAGE_ERROR:
            err, debug = message.parse_error()
            log( "Error: %s %s" % (err, debug) )
            self.stop_playing()

        elif t == gst.MESSAGE_STATE_CHANGED:
            if ( message.src == self.player and
                message.structure['new-state'] == gst.STATE_PLAYING ):

                if self.want_to_seek:
                    # This only gets called when the file is first loaded
                    pause_time = self.playlist.play()
                    self.do_seek(from_beginning=pause_time)
                else:
                    self.set_controls_sensitivity(True)

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
                log('Error setting coverart...', exception=e)

        tag_vals = dict([ (i,'') for i in tags.keys()])
        for tag,value in tag_message.iteritems():
            if tags.has_key(tag) and value is not None and value.strip():
                tags[tag].set_markup('<big>'+value+'</big>')
                tag_vals[tag] = value
                tags[tag].set_alignment( 0.5*int(not self.has_coverart), 0.5)
                tags[tag].show()
            if tag == 'title':
                if running_on_tablet:
                    self.main_window.set_title(value)
                    # oh man this is hacky :(
                    if self.has_coverart:
                        tags[tag].set_size_request(420,-1)
                        if len(value) >= 80: value = value[:80] + '...'
                else:
                    self.main_window.set_title('Panucci - ' + value)

                tags[tag].set_markup('<b><big>'+value+'</big></b>')

    def demuxer_callback(self, demuxer, pad):
        adec_pad = self.audio_decoder.get_pad("sink")
        pad.link(adec_pad)

    def seekbutton_callback( self, widget, seek_amount ):
        self.do_seek(from_current=seek_amount*10**9)

    def bookmarks_callback(self, w):
        BookmarksWindow(self)


def run(filename=None):
    session_bus = dbus.SessionBus(mainloop=dbus.glib.DBusGMainLoop())
    bus_name = dbus.service.BusName('org.panucci', bus=session_bus)
    GTK_Main(bus_name, filename)
    gtk.main()

if __name__ == '__main__':
    log( 'WARNING: Use the "panucci" executable to run this program.' )
    log( 'Exiting...' )

