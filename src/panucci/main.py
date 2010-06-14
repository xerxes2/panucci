#!/usr/bin/env python
# -*- coding: utf-8 -*-
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
# Based on http://thpinfo.com/2008/panucci/:
#  A resuming media player for Podcasts and Audiobooks
#  Copyright (c) 2008-05-26 Thomas Perl <thpinfo.com>
#  (based on http://pygstdocs.berlios.de/pygst-tutorial/seeking.html)
#

from __future__ import absolute_import


import logging
import sys
import os, os.path
import time

import gtk
import gobject
import pango

import cgi

import panucci

from panucci import widgets
from panucci import util
from panucci import platform

log = logging.getLogger('panucci.panucci')

try:
    import pynotify
    pynotify.init('Panucci')
    have_pynotify = True
except:
    have_pynotify = False

try:
    import hildon
except:
    if platform.MAEMO:
        log.critical( 'Using GTK widgets, install "python2.5-hildon" '
            'for this to work properly.' )

from panucci.settings import settings
from panucci.player import player
from panucci.dbusinterface import interface
from panucci.services import ObservableService

about_name = 'Panucci'
about_text = _('Resuming audiobook and podcast player')
about_authors = ['Thomas Perl', 'Nick (nikosapi)', 'Matthew Taylor']
about_website = 'http://gpodder.org/panucci/'
about_bugtracker = 'http://bugs.maemo.org/enter_bug.cgi?product=Panucci'
about_donate = 'http://gpodder.org/donate'
about_copyright = '© 2008-2010 Thomas Perl and the Panucci Team'

coverart_sizes = {
    'normal'            : 110,
    'maemo'             : 200,
    'maemo fullscreen'  : 275,
}

gtk.icon_size_register('panucci-button', 32, 32)

def find_image(filename):
    bin_dir = os.path.dirname(sys.argv[0])
    locations = [
            os.path.join(bin_dir, '..', 'share', 'panucci'),
            os.path.join(bin_dir, '..', 'icons'),
            '/opt/panucci',
    ]

    for location in locations:
        fn = os.path.abspath(os.path.join(location, filename))
        if os.path.exists(fn):
            return fn

def generate_image(filename, is_stock=False):
    image = None
    if is_stock:
        image = gtk.image_new_from_stock(
            filename, gtk.icon_size_from_name('panucci-button') )
    else:
        filename = find_image(filename)
        if filename is not None:
            image = gtk.image_new_from_file(filename)
    if image is not None:
        if platform.MAEMO:
            image.set_padding(20, 20)
        else:
            image.set_padding(5, 5)
        image.show()
    return image

def image(widget, filename, is_stock=False):
    child = widget.get_child()
    if child is not None:
        widget.remove(child)
    image = generate_image(filename, is_stock)
    if image is not None:
        widget.add(image)

def dialog( toplevel_window, title, question, description,
            affirmative_button=gtk.STOCK_YES, negative_button=gtk.STOCK_NO,
            abortion_button=gtk.STOCK_CANCEL ):

    """Present the user with a yes/no/cancel dialog.
    The return value is either True, False or None, depending on which
    button has been pressed in the dialog:

        affirmative button (default: Yes)    => True
        negative button    (defaut: No)      => False
        abortion button    (default: Cancel) => None

    When the dialog is closed with the "X" button in the window manager
    decoration, the return value is always None (same as abortion button).

    You can set any of the affirmative_button, negative_button or
    abortion_button values to "None" to hide the corresponding action.
    """
    dlg = gtk.MessageDialog( toplevel_window, gtk.DIALOG_MODAL,
                             gtk.MESSAGE_QUESTION, message_format=question )

    dlg.set_title(title)

    if abortion_button is not None:
        dlg.add_button(abortion_button, gtk.RESPONSE_CANCEL)
    if negative_button is not None:
        dlg.add_button(negative_button, gtk.RESPONSE_NO)
    if affirmative_button is not None:
        dlg.add_button(affirmative_button, gtk.RESPONSE_YES)

    dlg.format_secondary_text(description)

    response = dlg.run()
    dlg.destroy()

    if response == gtk.RESPONSE_YES:
        return True
    elif response == gtk.RESPONSE_NO:
        return False
    elif response in [gtk.RESPONSE_CANCEL, gtk.RESPONSE_DELETE_EVENT]:
        return None

def get_file_from_filechooser(
    toplevel_window, folder=False, save_file=False, save_to=None):

    if folder:
        open_action = gtk.FILE_CHOOSER_ACTION_SELECT_FOLDER
    else:
        open_action = gtk.FILE_CHOOSER_ACTION_OPEN

    if platform.FREMANTLE:
        if save_file:
            dlg = gobject.new(hildon.FileChooserDialog, \
                    action=gtk.FILE_CHOOSER_ACTION_SAVE)
        else:
            dlg = gobject.new(hildon.FileChooserDialog, \
                    action=open_action)
    elif platform.MAEMO:
        if save_file:
            args = ( toplevel_window, gtk.FILE_CHOOSER_ACTION_SAVE )
        else:
            args = ( toplevel_window, open_action )

        dlg = hildon.FileChooserDialog( *args )
    else:
        if save_file:
            args = ( _('Select file to save playlist to'), None,
                gtk.FILE_CHOOSER_ACTION_SAVE,
                (( gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT,
                gtk.STOCK_SAVE, gtk.RESPONSE_OK )) )
        else:
            args = ( _('Select podcast or audiobook'), None, open_action,
                (( gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT,
                gtk.STOCK_OPEN, gtk.RESPONSE_OK )) )

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

def set_stock_button_text( button, text ):
    alignment = button.get_child()
    hbox = alignment.get_child()
    image, label = hbox.get_children()
    label.set_text(text)

##################################################
# PanucciGUI
##################################################
class PanucciGUI(object):
    """ The object that holds the entire panucci gui """

    def __init__(self, filename=None):
        self.__log = logging.getLogger('panucci.panucci.PanucciGUI')
        interface.register_gui(self)

        # Build the base ui (window and menubar)
        if platform.MAEMO:
            self.app = hildon.Program()
            if platform.FREMANTLE:
                window = hildon.StackableWindow()
            else:
                window = hildon.Window()
            self.app.add_window(window)
        else:
            window = gtk.Window(gtk.WINDOW_TOPLEVEL)

        self.main_window = window
        window.set_title('Panucci')
        self.window_icon = find_image('panucci.png')
        if self.window_icon is not None:
            window.set_icon_from_file( self.window_icon )
        window.set_default_size(400, -1)
        window.set_border_width(0)
        window.connect("destroy", self.destroy)

        # Add the tabs (they are private to prevent us from trying to do
        # something like gui_root.player_tab.some_function() from inside
        # playlist_tab or vice-versa)
        self.__player_tab = PlayerTab(self)
        self.__playlist_tab = PlaylistTab(self)

        if platform.FREMANTLE:
            self.playlist_window = hildon.StackableWindow()
        else:
            self.playlist_window = gtk.Window(gtk.WINDOW_TOPLEVEL)
        self.playlist_window.connect('delete-event', gtk.Widget.hide_on_delete)
        self.playlist_window.set_title(_('Playlist'))
        self.playlist_window.set_transient_for(self.main_window)
        self.playlist_window.add(self.__playlist_tab)

        self.create_actions()

        if platform.MAEMO:
            if platform.FREMANTLE:
                window.set_app_menu(self.create_app_menu())
            else:
                window.set_menu(self.create_menu())
            window.add(self.__player_tab)
        else:
            menu_vbox = gtk.VBox()
            menu_vbox.set_spacing(0)
            window.add(menu_vbox)
            menu_bar = gtk.MenuBar()
            self.create_desktop_menu(menu_bar)
            menu_vbox.pack_start(menu_bar, False, False, 0)
            menu_bar.show()
            menu_vbox.pack_end(self.__player_tab, True, True, 6)

        # Tie it all together!
        self.__ignore_queue_check = False
        self.__window_fullscreen = False

        if platform.MAEMO and interface.headset_device is not None:
            # Enable play/pause with headset button
            interface.headset_device.connect_to_signal(
                'Condition', self.handle_headset_button )

        self.main_window.connect('key-press-event', self.on_key_press)
        player.playlist.register( 'file_queued', self.on_file_queued )

        player.playlist.register( 'playlist-to-be-overwritten',
                                  self.check_queue )
        self.__player_tab.register( 'select-current-item-request',
                                    self.__select_current_item )

        self.main_window.show_all()

        # this should be done when the gui is ready
        player.init(filepath=filename)

        pos_int, dur_int = player.get_position_duration()
        # This prevents bogus values from being set while seeking
        if (pos_int > 10**9) and (dur_int > 10**9):
            self.set_progress_callback(pos_int, dur_int)

    def create_actions(self):
        self.action_open = gtk.Action('open', _('Open'), _('Open a file or playlist'), gtk.STOCK_OPEN)
        self.action_open.connect('activate', self.open_file_callback)
        self.action_save = gtk.Action('save', _('Save playlist'), _('Save current playlist to file'), gtk.STOCK_SAVE_AS)
        self.action_save.connect('activate', self.save_to_playlist_callback)
        self.action_playlist = gtk.Action('playlist', _('Playlist'), _('Open the current playlist'), None)
        self.action_playlist.connect('activate', lambda a: self.playlist_window.show())
        self.action_about = gtk.Action('about', _('About Panucci'), _('Show application version'), gtk.STOCK_ABOUT)
        self.action_about.connect('activate', self.about_callback)
        self.action_quit = gtk.Action('quit', _('Quit'), _('Close Panucci'), gtk.STOCK_QUIT)
        self.action_quit.connect('activate', self.destroy)

    def create_desktop_menu(self, menu_bar):
        file_menu_item = gtk.MenuItem(_('File'))
        file_menu = gtk.Menu()
        file_menu.append(self.action_open.create_menu_item())
        file_menu.append(self.action_save.create_menu_item())
        file_menu.append(gtk.SeparatorMenuItem())
        file_menu.append(self.action_quit.create_menu_item())
        file_menu_item.set_submenu(file_menu)
        menu_bar.append(file_menu_item)

        tools_menu_item = gtk.MenuItem(_('Tools'))
        tools_menu = gtk.Menu()
        tools_menu.append(self.action_playlist.create_menu_item())
        tools_menu_item.set_submenu(tools_menu)
        menu_bar.append(tools_menu_item)

        help_menu_item = gtk.MenuItem(_('Help'))
        help_menu = gtk.Menu()
        help_menu.append(self.action_about.create_menu_item())
        help_menu_item.set_submenu(help_menu)
        menu_bar.append(help_menu_item)

    def create_app_menu(self):
        menu = hildon.AppMenu()

        b = gtk.Button(_('Playlist'))
        b.connect('clicked', lambda b: self.__player_tab.notify('select-current-item-request'))
        menu.append(b)

        b = gtk.Button(_('About'))
        b.connect('clicked', self.about_callback)
        menu.append(b)

        menu.show_all()
        return menu

    def create_menu(self):
        # the main menu
        menu = gtk.Menu()

        menu_open = gtk.ImageMenuItem(_('Open playlist'))
        menu_open.set_image(
            gtk.image_new_from_stock(gtk.STOCK_OPEN, gtk.ICON_SIZE_MENU))
        menu_open.connect("activate", self.open_file_callback)
        menu.append(menu_open)

        # the recent files menu
        self.menu_recent = gtk.MenuItem(_('Open recent playlist'))
        menu.append(self.menu_recent)
        self.create_recent_files_menu()

        menu.append(gtk.SeparatorMenuItem())

        menu_save = gtk.ImageMenuItem(_('Save current playlist'))
        menu_save.set_image(
            gtk.image_new_from_stock(gtk.STOCK_SAVE_AS, gtk.ICON_SIZE_MENU))
        menu_save.connect("activate", self.save_to_playlist_callback)
        menu.append(menu_save)

        menu.append(gtk.SeparatorMenuItem())

        # the settings sub-menu
        menu_settings = gtk.MenuItem(_('Settings'))
        menu.append(menu_settings)

        menu_settings_sub = gtk.Menu()
        menu_settings.set_submenu(menu_settings_sub)

        menu_settings_enable_dual_action = gtk.CheckMenuItem(
            _('Enable dual-action buttons') )
        settings.attach_checkbutton( menu_settings_enable_dual_action,
                                     'enable_dual_action_btn' )
        menu_settings_sub.append(menu_settings_enable_dual_action)

        menu_settings_lock_progress = gtk.CheckMenuItem(_('Lock Progress Bar'))
        settings.attach_checkbutton( menu_settings_lock_progress,
                                     'progress_locked' )
        menu_settings_sub.append(menu_settings_lock_progress)

        menu_about = gtk.ImageMenuItem(gtk.STOCK_ABOUT)
        menu_about.connect("activate", self.about_callback)
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

        if len(self.recent_files) > 0:
            for f in self.recent_files:
                # don't include the temporary playlist in the file list
                if f == panucci.PLAYLIST_FILE: continue
                # don't include non-existant files
                if not os.path.exists( f ): continue
                filename, extension = os.path.splitext(os.path.basename(f))
                menu_item = gtk.MenuItem( filename.replace('_', ' '))
                menu_item.connect('activate', self.on_recent_file_activate, f)
                menu_recent_sub.append(menu_item)
        else:
            menu_item = gtk.MenuItem(_('No recent files available.'))
            menu_item.set_sensitive(False)
            menu_recent_sub.append(menu_item)

        self.menu_recent.set_submenu(menu_recent_sub)

    def notify(self, message):
        """ Sends a notification using pynotify, returns message """
        if platform.DESKTOP and have_pynotify:
            icon = find_image('panucci_64x64.png')
            notification = pynotify.Notification(self.main_window.get_title(), message, icon)
            notification.show()
        elif platform.FREMANTLE:
            hildon.hildon_banner_show_information(self.main_window, \
                    '', message)
        elif platform.MAEMO:
            # Note: This won't work if we're not in the gtk main loop
            markup = '<b>%s</b>\n<small>%s</small>' % (self.main_window.get_title(), message)
            hildon.hildon_banner_show_information_with_markup(self.main_window, None, markup)

    def destroy(self, widget):
        widget.hide()
        player.quit()
        gtk.main_quit()

    def set_progress_indicator(self, loading_title=False):
        if platform.FREMANTLE:
            if loading_title:
                self.main_window.set_title(_('Loading...'))
            hildon.hildon_gtk_window_set_progress_indicator(self.main_window, \
                    True)
            while gtk.events_pending():
                gtk.main_iteration(False)

    def show_main_window(self):
        self.main_window.present()

    def check_queue(self):
        """ Makes sure the queue is saved if it has been modified
                True means a new file can be opened
                False means the user does not want to continue """

        if not self.__ignore_queue_check and player.playlist.queue_modified:
            response = dialog(
                self.main_window, _('Save current playlist'),
                _('Current playlist has been modified'),
                _('Opening a new file will replace the current playlist. ') +
                _('Do you want to save it before creating a new one?'),
                affirmative_button=gtk.STOCK_SAVE,
                negative_button=_('Discard changes'))

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
            # set __ingnore__queue_check because we already did the check
            self.__ignore_queue_check = True
            filename = get_file_from_filechooser(self.main_window)
            if filename is not None:
                self._play_file(filename)

            self.__ignore_queue_check = False

    def save_to_playlist_callback(self, widget=None):
        filename = get_file_from_filechooser(
            self.main_window, save_file=True, save_to='playlist.m3u' )

        if filename is None:
            return False

        if os.path.isfile(filename):
            response = dialog( self.main_window, _('File already exists'),
                _('File already exists'),
                _('The file %s already exists. You can choose another name or '
                  'overwrite the existing file.') % os.path.basename(filename),
                affirmative_button=gtk.STOCK_SAVE,
                negative_button=_('Rename file'))

            if response is None:
                return None

            elif response:
                pass
            elif not response:
                return self.save_to_playlist_callback()

        ext = util.detect_filetype(filename)
        if not player.playlist.save_to_new_playlist(filename, ext):
            self.notify(_('Error saving playlist...'))
            return False

        return True

    def __get_fullscreen(self):
        return self.__window_fullscreen

    def __set_fullscreen(self, value):
        if value != self.__window_fullscreen:
            if value:
                self.main_window.fullscreen()
            else:
                self.main_window.unfullscreen()

            self.__window_fullscreen = value
            player.playlist.send_metadata()

    fullscreen = property( __get_fullscreen, __set_fullscreen )

    def on_key_press(self, widget, event):
        if platform.MAEMO:
            if event.keyval == gtk.keysyms.F6:
                self.fullscreen = not self.fullscreen

    def on_recent_file_activate(self, widget, filepath):
        self._play_file(filepath)

    def on_file_queued(self, filepath, success, notify):
        if notify:
            filename = os.path.basename(filepath)
            if success:
                self.__log.info(
                    self.notify( '%s added successfully.' % filename ))
            else:
                self.__log.error(
                    self.notify( 'Error adding %s to the queue.' % filename))

    def about_callback(self, widget):
        if platform.FREMANTLE:
            from panucci.aboutdialog import HeAboutDialog

            HeAboutDialog.present(self.main_window,
                    about_name,
                    'panucci',
                    panucci.__version__,
                    about_text,
                    about_copyright,
                    about_website,
                    about_bugtracker,
                    about_donate)
        else:
            about = gtk.AboutDialog()
            about.set_transient_for(self.main_window)
            about.set_name(about_name)
            about.set_version(panucci.__version__)
            about.set_copyright(about_copyright)
            about.set_comments(about_text)
            about.set_website(about_website)
            about.set_authors(about_authors)
            about.set_translator_credits(_('translator-credits'))
            about.set_logo_icon_name('panucci')
            about.run()
            about.destroy()

    def _play_file(self, filename, pause_on_load=False):
        player.playlist.load( os.path.abspath(filename) )

        if player.playlist.is_empty:
            return False

    def handle_headset_button(self, event, button):
        if event == 'ButtonPressed' and button == 'phone':
            player.play_pause_toggle()

    def __select_current_item( self ):
        # Select the currently playing track in the playlist tab
        # and switch to it (so we can edit bookmarks, etc.. there)
        self.__playlist_tab.select_current_item()
        self.playlist_window.show()

##################################################
# PlayerTab
##################################################
class PlayerTab(ObservableService, gtk.HBox):
    """ The tab that holds the player elements """

    signals = [ 'select-current-item-request', ]

    def __init__(self, gui_root):
        self.__log = logging.getLogger('panucci.panucci.PlayerTab')
        self.__gui_root = gui_root

        gtk.HBox.__init__(self)
        ObservableService.__init__(self, self.signals, self.__log)

        # Timers
        self.progress_timer_id = None

        self.recent_files = []
        self.make_player_tab()
        self.has_coverart = False

        #settings.register( 'enable_dual_action_btn_changed',
        #                   self.on_dual_action_setting_changed )
        #settings.register( 'dual_action_button_delay_changed',
        #                   self.on_dual_action_setting_changed )
        #settings.register( 'scrolling_labels_changed', lambda v:
        #                   setattr( self.title_label, 'scrolling', v ) )

        player.register( 'stopped', self.on_player_stopped )
        player.register( 'playing', self.on_player_playing )
        player.register( 'paused', self.on_player_paused )
        player.playlist.register( 'end-of-playlist',
                                  self.on_player_end_of_playlist )
        player.playlist.register( 'new-track-loaded',
                                  self.on_player_new_track )
        player.playlist.register( 'new-metadata-available',
                                  self.on_player_new_metadata )

    def make_player_tab(self):
        main_vbox = gtk.VBox()
        main_vbox.set_spacing(6)
        # add a vbox to self
        self.pack_start(main_vbox, True, True)

        # a hbox to hold the cover art and metadata vbox
        metadata_hbox = gtk.HBox()
        metadata_hbox.set_spacing(6)
        main_vbox.pack_start(metadata_hbox, True, False)

        self.cover_art = gtk.Image()
        metadata_hbox.pack_start( self.cover_art, False, False )

        # vbox to hold metadata
        metadata_vbox = gtk.VBox()
        metadata_vbox.pack_start(gtk.Image(), True, True)
        self.artist_label = gtk.Label('')
        self.artist_label.set_ellipsize(pango.ELLIPSIZE_END)
        metadata_vbox.pack_start(self.artist_label, False, False)
        self.album_label = gtk.Label('')
        if platform.FREMANTLE:
            hildon.hildon_helper_set_logical_font(self.album_label, 'SmallSystemFont')
            hildon.hildon_helper_set_logical_color(self.album_label, gtk.RC_FG, gtk.STATE_NORMAL, 'SecondaryTextColor')
        else:
            self.album_label.modify_font(pango.FontDescription('normal 8'))
        self.album_label.set_ellipsize(pango.ELLIPSIZE_END)
        metadata_vbox.pack_start(self.album_label, False, False)
        self.title_label = widgets.ScrollingLabel('',
                                                  update_interval=100,
                                                  pixel_jump=1,
                                                  delay_btwn_scrolls=5000,
                                                  delay_halfway=3000)
        self.title_label.scrolling = settings.scrolling_labels
        metadata_vbox.pack_start(self.title_label, False, False)
        metadata_vbox.pack_start(gtk.Image(), True, True)
        metadata_hbox.pack_start( metadata_vbox, True, True )

        progress_eventbox = gtk.EventBox()
        progress_eventbox.set_events(gtk.gdk.BUTTON_PRESS_MASK)
        progress_eventbox.connect(
            'button-press-event', self.on_progressbar_changed )
        self.progress = gtk.ProgressBar()
        # make the progress bar more "finger-friendly"
        if platform.FREMANTLE:
            self.progress.set_size_request(-1, 100)
        elif platform.MAEMO:
            self.progress.set_size_request(-1, 50)
        progress_eventbox.add(self.progress)
        main_vbox.pack_start( progress_eventbox, False, False )

        # make the button box
        buttonbox = gtk.HBox()

        # A wrapper to help create DualActionButtons with the right settings
        def create_da(widget, action, widget2=None, action2=None):
            if platform.FREMANTLE:
                widget2 = None
                action2 = None

            return widgets.DualActionButton(widget, action, \
                    widget2, action2, \
                    settings.dual_action_button_delay, \
                    settings.enable_dual_action_btn)

        self.rrewind_button = create_da(
                generate_image('media-skip-backward.png'),
                lambda: self.do_seek(-1*settings.seek_long),
                generate_image(gtk.STOCK_GOTO_FIRST, True),
                player.playlist.prev)
        buttonbox.add(self.rrewind_button)

        self.rewind_button = create_da(
                generate_image('media-seek-backward.png'),
                lambda: self.do_seek(-1*settings.seek_short))
        buttonbox.add(self.rewind_button)

        self.play_pause_button = gtk.Button('')
        image(self.play_pause_button, 'media-playback-start.png')
        self.play_pause_button.connect( 'clicked',
                                        self.on_btn_play_pause_clicked )
        self.play_pause_button.set_sensitive(False)
        buttonbox.add(self.play_pause_button)

        self.forward_button = create_da(
                generate_image('media-seek-forward.png'),
                lambda: self.do_seek(settings.seek_short))
        buttonbox.add(self.forward_button)

        self.fforward_button = create_da(
                generate_image('media-skip-forward.png'),
                lambda: self.do_seek(settings.seek_long),
                generate_image(gtk.STOCK_GOTO_LAST, True),
                player.playlist.next)
        buttonbox.add(self.fforward_button)

        self.bookmarks_button = create_da(
                generate_image('bookmark-new.png'),
                player.add_bookmark_at_current_position,
                generate_image(gtk.STOCK_JUMP_TO, True),
                lambda *args: self.notify('select-current-item-request'))
        buttonbox.add(self.bookmarks_button)
        self.set_controls_sensitivity(False)

        if platform.FREMANTLE:
            for child in buttonbox.get_children():
                if isinstance(child, gtk.Button):
                    child.set_name('HildonButton-thumb')
            buttonbox.set_size_request(-1, 105)

        main_vbox.pack_start(buttonbox, False, False)

        if platform.MAEMO:
            self.__gui_root.main_window.connect( 'key-press-event',
                                                 self.on_key_press )

            # Disable focus for all widgets, so we can use the cursor
            # keys + enter to directly control our media player, which
            # is handled by "key-press-event"
            for w in (
                    self.rrewind_button, self.rewind_button,
                    self.play_pause_button, self.forward_button,
                    self.fforward_button, self.progress,
                    self.bookmarks_button, ):
                w.unset_flags(gtk.CAN_FOCUS)

    def set_controls_sensitivity(self, sensitive):
        for button in self.forward_button, self.rewind_button, \
                      self.fforward_button, self.rrewind_button:

            button.set_sensitive(sensitive)

        # the play/pause button should always be available except
        # for when the player starts without a file
        self.play_pause_button.set_sensitive(True)

    def on_dual_action_setting_changed( self, *args ):
        for button in self.forward_button, self.rewind_button, \
                      self.fforward_button, self.rrewind_button, \
                      self.bookmarks_button:

            button.set_longpress_enabled( settings.enable_dual_action_btn )
            button.set_duration( settings.dual_action_button_delay )

    def on_key_press(self, widget, event):
        if platform.MAEMO:
            if event.keyval == gtk.keysyms.Left: # seek back
                self.do_seek( -1 * settings.seek_long )
            elif event.keyval == gtk.keysyms.Right: # seek forward
                self.do_seek( settings.seek_long )
            elif event.keyval == gtk.keysyms.Return: # play/pause
                self.on_btn_play_pause_clicked()

    def on_player_stopped(self):
        self.stop_progress_timer()
        self.set_controls_sensitivity(False)
        image(self.play_pause_button, 'media-playback-start.png')

    def on_player_playing(self):
        self.start_progress_timer()
        image(self.play_pause_button, 'media-playback-pause.png')
        self.set_controls_sensitivity(True)
        if platform.FREMANTLE:
            hildon.hildon_gtk_window_set_progress_indicator(\
                    self.__gui_root.main_window, False)

    def on_player_new_track(self):
        for widget in [self.title_label,self.artist_label,self.album_label]:
            widget.set_markup('')
            widget.hide()

        self.cover_art.hide()
        self.has_coverart = False

    def on_player_new_metadata(self):
        metadata = player.playlist.get_file_metadata()
        self.set_metadata(metadata)

        if not player.playing:
            position = player.playlist.get_current_position()
            estimated_length = metadata.get('length', 0)
            self.set_progress_callback( position, estimated_length )

    def on_player_paused( self, position, duration ):
        self.stop_progress_timer() # This should save some power
        self.set_progress_callback( position, duration )
        image(self.play_pause_button, 'media-playback-start.png')

    def on_player_end_of_playlist(self, loop):
        pass

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
        if ( not settings.progress_locked and
                event.type == gtk.gdk.BUTTON_PRESS and event.button == 1 ):
            new_fraction = event.x/float(widget.get_allocation().width)
            resp = player.do_seek(percent=new_fraction)
            if resp:
                # Preemptively update the progressbar to make seeking smoother
                self.set_progress_callback( *resp )

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

    def get_coverart_size( self ):
        if platform.MAEMO:
            if self.__gui_root.fullscreen:
                size = coverart_sizes['maemo fullscreen']
            else:
                size = coverart_sizes['maemo']
        else:
            size = coverart_sizes['normal']

        return size, size

    def set_coverart( self, pixbuf ):
        self.cover_art.set_from_pixbuf(pixbuf)
        self.cover_art.show()
        self.has_coverart = True

    def set_metadata( self, tag_message ):
        tags = { 'title': self.title_label, 'artist': self.artist_label,
                 'album': self.album_label }

        # set the coverart
        if tag_message.has_key('image') and tag_message['image'] is not None:
            value = tag_message['image']

            pbl = gtk.gdk.PixbufLoader()
            try:
                pbl.write(value)
                pbl.close()

                x, y = self.get_coverart_size()
                pixbuf = pbl.get_pixbuf()
                pixbuf = pixbuf.scale_simple( x, y, gtk.gdk.INTERP_BILINEAR )
                self.set_coverart(pixbuf)
            except Exception, e:
                self.__log.exception('Error setting coverart...')

        # set the text metadata
        for tag,value in tag_message.iteritems():
            if tags.has_key(tag) and value is not None and value.strip():
                try:
                    tags[tag].set_markup('<big>'+cgi.escape(value)+'</big>')
                except TypeError, e:
                    self.__log.exception(str(e))
                tags[tag].set_alignment( 0.5*int(not self.has_coverart), 0.5)
                tags[tag].show()

            if tag == 'title':
                # make the title bold
                tags[tag].set_markup('<b><big>'+cgi.escape(value)+'</big></b>')

                if not platform.MAEMO:
                    value += ' - Panucci'

                if platform.FREMANTLE and len(value) > 25:
                    value = value[:24] + '...'

                self.__gui_root.main_window.set_title( value )

    def do_seek(self, seek_amount):
        resp = player.do_seek(from_current=seek_amount*10**9)
        if resp:
            # Preemptively update the progressbar to make seeking smoother
            self.set_progress_callback( *resp )



##################################################
# PlaylistTab
##################################################
class PlaylistTab(gtk.VBox):
    def __init__(self, main_window):
        gtk.VBox.__init__(self)
        self.__log = logging.getLogger('panucci.panucci.BookmarksWindow')
        self.main = main_window

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
        set_stock_button_text( self.add_button, _('Add File') )
        self.add_button.connect('clicked', self.add_file)
        self.hbox.pack_start(self.add_button, True, True)

        self.dir_button = gtk.Button(gtk.STOCK_OPEN)
        self.dir_button.set_use_stock(True)
        set_stock_button_text( self.dir_button, _('Add Directory') )
        self.dir_button.connect('clicked', self.add_directory)
        self.hbox.pack_start(self.dir_button, True, True)

        self.remove_button = gtk.Button(gtk.STOCK_REMOVE)
        self.remove_button.set_use_stock(True)
        self.remove_button.connect('clicked', self.remove_bookmark)
        self.hbox.pack_start(self.remove_button, True, True)

        self.jump_button = gtk.Button(gtk.STOCK_JUMP_TO)
        self.jump_button.set_use_stock(True)
        self.jump_button.connect('clicked', self.jump_bookmark)
        self.hbox.pack_start(self.jump_button, True, True)

        self.info_button = gtk.Button()
        self.info_button.add(
                gtk.image_new_from_stock(gtk.STOCK_INFO, gtk.ICON_SIZE_BUTTON))
        self.info_button.connect('clicked', self.show_playlist_item_details)
        self.hbox.pack_start(self.info_button, True, True)

        if platform.FREMANTLE:
            for child in self.hbox.get_children():
                if isinstance(child, gtk.Button):
                    child.set_name('HildonButton-thumb')
            self.hbox.set_size_request(-1, 105)

        self.pack_start(self.hbox, False, True)

        player.playlist.register( 'file_queued',
                                  lambda x,y,z: self.update_model() )
        player.playlist.register( 'bookmark_added', self.on_bookmark_added )

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
                player.playlist.move_item( from_row, to_row )

        else:
            self.__log.debug('No drop_data or selection.data available')

    def update_model(self):
        plist = player.playlist
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
                player.playlist.update_bookmark(
                    item_id, bkmk_id, name=new_text )
        else:
            self.__model.set_value(iter, 1, old_text)

    def on_bookmark_added(self, parent_id, bookmark_name, position):
        self.main.notify(_('Bookmark added: %s') % bookmark_name)
        self.update_model()

    def add_file(self, widget):
        filename = get_file_from_filechooser(self.main.main_window)
        if filename is not None:
            player.playlist.append(filename)

    def add_directory(self, widget):
        directory = get_file_from_filechooser(
            self.main.main_window, folder=True )
        if directory is not None:
            player.playlist.load_directory(directory, append=True)

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
            player.playlist.remove_bookmark( item_id, bkmk_id )
            if bkmk_iter is not None:
                model.remove(bkmk_iter)
            elif item_iter is not None:
                model.remove(item_iter)

    def select_current_item(self):
        model = self.treeview.get_model()
        selection = self.treeview.get_selection()
        current_item_id = str(player.playlist.get_current_item())
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
            playlist_item = player.playlist.get_item_by_id(item_id)
            PlaylistItemDetails(self.main, playlist_item)

    def jump_bookmark(self, w):
        selected = list(self.__cur_selection())
        if len(selected) == 1:
            # It should be guranteed by the fact that we only enable the
            # "Jump to" button when the selection count equals 1.
            model, bkmk_id, bkmk_iter, item_id, item_iter = selected.pop(0)
            player.playlist.load_from_bookmark_id(item_id, bkmk_id)

            # FIXME: The player/playlist should be able to take care of this
            if not player.playing:
                player.play()


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


def run(filename=None):
    PanucciGUI(filename)
    gtk.main()

if __name__ == '__main__':
    log.error( 'Use the "panucci" executable to run this program.' )
    log.error( 'Exiting...' )
    sys.exit(1)

