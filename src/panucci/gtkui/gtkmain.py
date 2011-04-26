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

from __future__ import absolute_import

import logging
import os.path
import cgi
import gtk
import gobject
import pango

import panucci
from panucci import util
from panucci import platform
from panucci import playlist
from panucci.dbusinterface import interface
from panucci.services import ObservableService
from panucci.gtkui import gtkwidgets as widgets
from panucci.gtkui import gtkplaylist
from panucci.gtkui import gtkutil

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
        log = logging.getLogger('panucci.panucci')
        log.critical( 'Using GTK widgets, install "python2.5-hildon" '
            'for this to work properly.' )

if platform.FREMANTLE:
    # Workaround Maemo bug 6694 (Playback in Silent mode)
    gobject.set_application_name('FMRadio')

gtk.icon_size_register('panucci-button', 32, 32)

##################################################
# PanucciGUI
##################################################
class PanucciGUI(object):
    """ The object that holds the entire panucci gui """

    def __init__(self, settings, filename=None):
        self.__log = logging.getLogger('panucci.panucci.PanucciGUI')
        interface.register_gui(self)
        self.config = settings.config
        self.playlist = playlist.Playlist(self.config)

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
        self.window_icon = util.find_data_file('panucci.png')
        if self.window_icon is not None:
            window.set_icon_from_file( self.window_icon )
        window.set_default_size(400, -1)
        window.set_border_width(0)
        window.connect("destroy", self.destroy)

        # Add the tabs (they are private to prevent us from trying to do
        # something like gui_root.player_tab.some_function() from inside
        # playlist_tab or vice-versa)
        self.__player_tab = PlayerTab(self)
        self.__playlist_tab = gtkplaylist.PlaylistTab(self, self.playlist)

        self.create_actions()

        if platform.FREMANTLE:
            self.playlist_window = hildon.StackableWindow()
            self.playlist_window.set_app_menu(self.create_playlist_app_menu())
        else:
            self.playlist_window = gtk.Window(gtk.WINDOW_TOPLEVEL)
        self.playlist_window.connect('delete-event', gtk.Widget.hide_on_delete)
        self.playlist_window.set_title(_('Playlist'))
        self.playlist_window.set_transient_for(self.main_window)
        self.playlist_window.add(self.__playlist_tab)

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

        if platform.MAEMO and interface.headset_device:
            # Enable play/pause with headset button
            import dbus
            interface.headset_device.connect_to_signal('Condition', \
                    self.handle_headset_button)
            system_bus = dbus.SystemBus()

            PATH = '/org/freedesktop/Hal/devices/computer_logicaldev_input_1'
            # Monitor connection state of BT headset
            system_bus.add_signal_receiver(self.handle_connection_state, 'DeviceAdded', \
                    'org.freedesktop.Hal.Manager', None, '/org/freedesktop/Hal/Manager')

            # Monitor BT headset buttons
            system_bus.add_signal_receiver(self.handle_bt_button, 'Condition', \
                    'org.freedesktop.Hal.Device', None, PATH)

        self.main_window.connect('key-press-event', self.on_key_press)
        self.playlist.register( 'file_queued', self.on_file_queued )

        self.playlist.register( 'playlist-to-be-overwritten',
                                  self.check_queue )
        self.__player_tab.register( 'select-current-item-request',
                                    self.__select_current_item )

        self.main_window.show_all()

        # this should be done when the gui is ready
        self.playlist.init(filepath=filename)

        pos_int, dur_int = self.playlist.player.get_position_duration()
        # This prevents bogus values from being set while seeking
        if (pos_int > 10**9) and (dur_int > 10**9):
            self.set_progress_callback(pos_int, dur_int)

        gtk.main()

    def create_actions(self):
        # File menu
        self.action_open = gtk.Action('open_file', _('Add File'), _('Open a file or playlist'), gtk.STOCK_NEW)
        self.action_open.connect('activate', self.open_file_callback)
        self.action_open_dir = gtk.Action('open_dir', _('Add Folder'), _('Open a directory'), gtk.STOCK_OPEN)
        self.action_open_dir.connect('activate', self.open_dir_callback)
        self.action_save = gtk.Action('save', _('Save Playlist'), _('Save current playlist to file'), gtk.STOCK_SAVE_AS)
        self.action_save.connect('activate', self.save_to_playlist_callback)
        self.action_empty_playlist = gtk.Action('empty_playlist', _('Clear Playlist'), _('Clear current playlist'), gtk.STOCK_DELETE)
        self.action_empty_playlist.connect('activate', self.empty_playlist_callback)
        self.action_delete_bookmarks = gtk.Action('delete_bookmarks', _('Delete All Bookmarks'), _('Deleting all bookmarks'), gtk.STOCK_DELETE)
        self.action_delete_bookmarks.connect('activate', self.delete_all_bookmarks_callback)
        self.action_quit = gtk.Action('quit', _('Quit'), _('Close Panucci'), gtk.STOCK_QUIT)
        self.action_quit.connect('activate', self.destroy)
        # Tools menu
        self.action_playlist = gtk.Action('playlist', _('Playlist'), _('Open the current playlist'), None)
        self.action_playlist.connect('activate', lambda a: self.playlist_window.show())
        self.action_settings = gtk.Action('settings', _('Settings'), _('Open the settings dialog'), None)
        self.action_settings.connect('activate', self.settings_callback)
        self.action_timer = gtk.Action('timer', _('Sleep Timer'), _('Start a timed shutdown'), None)
        self.action_timer.connect('activate', self.create_timer_dialog)
        self.action_fm = gtk.Action('fm', _('FM Transmitter'), _('Show FM transmitter dialog'), None)
        self.action_fm.connect('activate', self.show_fm_transmitter)
        # Settings menu
        self.action_lock_progress = gtk.ToggleAction('lock_progress', _('Lock Progress Bar'), None, None)
        self.action_lock_progress.connect("activate", self.set_boolean_config_callback)
        self.action_lock_progress.set_active(self.config.getboolean("options", "lock_progress"))
        self.action_dual_action_button = gtk.ToggleAction('dual_action_button', _('Dual Action Button'), None, None)
        self.action_dual_action_button.connect("activate", self.set_boolean_config_callback)
        self.action_dual_action_button.set_active(self.config.getboolean("options", "dual_action_button"))
        self.action_stay_at_end = gtk.ToggleAction('stay_at_end', _('Stay at End'), None, None)
        self.action_stay_at_end.connect("activate", self.set_boolean_config_callback)
        self.action_stay_at_end.set_active(self.config.getboolean("options", "stay_at_end"))
        self.action_seek_back = gtk.ToggleAction('seek_back', _('Seek Back'), None, None)
        self.action_seek_back.connect("activate", self.set_boolean_config_callback)
        self.action_seek_back.set_active(self.config.getboolean("options", "seek_back"))
        self.action_scrolling_labels = gtk.ToggleAction('scrolling_labels', _('Scrolling Labels'), None, None)
        self.action_scrolling_labels.connect("activate", self.scrolling_labels_callback)
        self.action_scrolling_labels.set_active(self.config.getboolean("options", "scrolling_labels"))
        self.action_play_on_headset = gtk.ToggleAction('play_on_headset', _('Play on Headset'), None, None)
        self.action_play_on_headset.connect("activate", self.set_boolean_config_callback)
        self.action_play_on_headset.set_active(self.config.getboolean("options", "play_on_headset"))
        self.action_play_mode = gtk.Action('play_mode', _('Play Mode'), None, None)
        self.action_play_mode_all = gtk.RadioAction('all', _('All'), None, None, 0)
        self.action_play_mode_all.connect("activate", self.set_play_mode_callback)
        self.action_play_mode_single = gtk.RadioAction('single', _('Single'), None, None, 1)
        self.action_play_mode_single.connect("activate", self.set_play_mode_callback)
        self.action_play_mode_single.set_group(self.action_play_mode_all)
        self.action_play_mode_random = gtk.RadioAction('random', _('Random'), None, None, 1)
        self.action_play_mode_random.connect("activate", self.set_play_mode_callback)
        self.action_play_mode_random.set_group(self.action_play_mode_all)
        self.action_play_mode_repeat = gtk.RadioAction('repeat', _('Repeat'), None, None, 1)
        self.action_play_mode_repeat.connect("activate", self.set_play_mode_callback)
        self.action_play_mode_repeat.set_group(self.action_play_mode_all)
        if self.config.get("options", "play_mode") == "single":
            self.action_play_mode_single.set_active(True)
        elif self.config.get("options", "play_mode") == "random":
            self.action_play_mode_random.set_active(True)
        elif self.config.get("options", "play_mode") == "repeat":
            self.action_play_mode_repeat.set_active(True)
        else:
            self.action_play_mode_all.set_active(True)
        # Help menu
        self.action_about = gtk.Action('about', _('About'), _('Show application version'), gtk.STOCK_ABOUT)
        self.action_about.connect('activate', self.about_callback)

    def create_desktop_menu(self, menu_bar):
        file_menu_item = gtk.MenuItem(_('File'))
        file_menu = gtk.Menu()
        file_menu.append(self.action_open.create_menu_item())
        file_menu.append(self.action_open_dir.create_menu_item())
        file_menu.append(self.action_save.create_menu_item())
        file_menu.append(self.action_empty_playlist.create_menu_item())
        file_menu.append(self.action_delete_bookmarks.create_menu_item())
        file_menu.append(gtk.SeparatorMenuItem())
        file_menu.append(self.action_quit.create_menu_item())
        file_menu_item.set_submenu(file_menu)
        menu_bar.append(file_menu_item)

        tools_menu_item = gtk.MenuItem(_('Tools'))
        tools_menu = gtk.Menu()
        tools_menu.append(self.action_playlist.create_menu_item())
        tools_menu.append(self.action_timer.create_menu_item())
        #tools_menu.append(self.action_fm.create_menu_item())
        tools_menu_item.set_submenu(tools_menu)
        menu_bar.append(tools_menu_item)

        settings_menu_item = gtk.MenuItem(_('Settings'))
        settings_menu = gtk.Menu()
        settings_menu.append(self.action_lock_progress.create_menu_item())
        settings_menu.append(self.action_dual_action_button.create_menu_item())
        settings_menu.append(self.action_stay_at_end.create_menu_item())
        settings_menu.append(self.action_seek_back.create_menu_item())
        settings_menu.append(self.action_scrolling_labels.create_menu_item())
        play_mode_menu_item = self.action_play_mode.create_menu_item()
        settings_menu.append(play_mode_menu_item)
        play_mode_menu = gtk.Menu()
        play_mode_menu_item.set_submenu(play_mode_menu)
        play_mode_menu.append(self.action_play_mode_all.create_menu_item())
        play_mode_menu.append(self.action_play_mode_single.create_menu_item())
        play_mode_menu.append(self.action_play_mode_random.create_menu_item())
        play_mode_menu.append(self.action_play_mode_repeat.create_menu_item())
        settings_menu_item.set_submenu(settings_menu)
        menu_bar.append(settings_menu_item)

        help_menu_item = gtk.MenuItem(_('Help'))
        help_menu = gtk.Menu()
        help_menu.append(self.action_about.create_menu_item())
        help_menu_item.set_submenu(help_menu)
        menu_bar.append(help_menu_item)

    def create_playlist_app_menu(self):
        menu = hildon.AppMenu()

        for action in (self.action_save,
                self.action_delete_bookmarks):
            b = gtk.Button()
            action.connect_proxy(b)
            menu.append(b)

        menu.show_all()
        return menu

    def create_app_menu(self):
        menu = hildon.AppMenu()

        for action in (self.action_settings,
                self.action_playlist,
                self.action_open,
                self.action_open_dir,
                self.action_empty_playlist,
                self.action_timer,
                self.action_fm,
                self.action_about):
            b = gtk.Button()
            action.connect_proxy(b)
            menu.append(b)

        menu.show_all()
        return menu

    def create_menu(self):
        # the main menu
        menu = gtk.Menu()

        menu_open = gtk.ImageMenuItem(_('Add File'))
        menu_open.set_image(
            gtk.image_new_from_stock(gtk.STOCK_NEW, gtk.ICON_SIZE_MENU))
        menu_open.connect("activate", self.open_file_callback)
        menu.append(menu_open)

        menu_open = gtk.ImageMenuItem(_('Add Folder'))
        menu_open.set_image(
            gtk.image_new_from_stock(gtk.STOCK_OPEN, gtk.ICON_SIZE_MENU))
        menu_open.connect("activate", self.open_dir_callback)
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

        menu_save = gtk.ImageMenuItem(_('Delete Playlist'))
        menu_save.set_image(
            gtk.image_new_from_stock(gtk.STOCK_DELETE, gtk.ICON_SIZE_MENU))
        menu_save.connect("activate", self.empty_playlist_callback)
        menu.append(menu_save)

        menu_save = gtk.ImageMenuItem(_('Delete All Bookmarks'))
        menu_save.set_image(
            gtk.image_new_from_stock(gtk.STOCK_DELETE, gtk.ICON_SIZE_MENU))
        menu_save.connect("activate", self.delete_all_bookmarks_callback)
        menu.append(menu_save)

        menu.append(gtk.SeparatorMenuItem())

        # the settings sub-menu
        menu_settings = gtk.MenuItem(_('Settings'))
        menu.append(menu_settings)

        menu_settings_sub = gtk.Menu()
        menu_settings.set_submenu(menu_settings_sub)

        menu_settings_enable_dual_action = gtk.CheckMenuItem(_('Enable dual-action buttons') )
        menu_settings_enable_dual_action.connect('toggled', self.set_dual_action_button_callback)
        menu_settings_enable_dual_action.set_active(self.config.getboolean("options", "dual_action_button"))
        menu_settings_sub.append(menu_settings_enable_dual_action)

        menu_settings_lock_progress = gtk.CheckMenuItem(_('Lock Progress Bar'))
        menu_settings_lock_progress.connect('toggled', self.lock_progress_callback)
        menu_settings_lock_progress.set_active(self.config.getboolean("options", "lock_progress"))
        menu_settings_sub.append(menu_settings_lock_progress)

        menu_about = gtk.ImageMenuItem(gtk.STOCK_ABOUT)
        menu_about.connect("activate", self.about_callback)
        menu.append(menu_about)

        menu.append(gtk.SeparatorMenuItem())

        menu_quit = gtk.ImageMenuItem(gtk.STOCK_QUIT)
        menu_quit.connect("activate", self.destroy)
        menu.append(menu_quit)

        return menu

    def create_timer_dialog(self,w):
        response = widgets.IntDialog.get_int(_("Sleep Timer"), _("Shutdown time in minutes"), 5, 1)
        if response[1]:
            gobject.timeout_add(60000*response[0], self.timed_shutdown)

    def timed_shutdown(self):
        self.destroy( None )
        return False

    def create_recent_files_menu( self ):
        max_files = self.config.getint("options", "max_recent_files")
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
            icon = util.find_data_file('panucci_64x64.png')
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
        self.main_window.hide()
        self.playlist.quit()
        util.write_config(self.config)
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

        if not self.__ignore_queue_check and self.playlist.queue_modified:
            response = gtkutil.dialog(
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
        # set __ingnore__queue_check because we already did the check
        self.__ignore_queue_check = True
        filename = gtkutil.get_file_from_filechooser(self)
        if filename is not None:
            self._play_file(filename)

        self.__ignore_queue_check = False

    def open_dir_callback(self, widget=None):
        filename = gtkutil.get_file_from_filechooser(self, folder=True)
        if filename is not None:
            self._play_file(filename)

    def save_to_playlist_callback(self, widget=None):
        filename = gtkutil.get_file_from_filechooser(
            self, save_file=True, save_to='playlist.m3u' )

        if filename is None:
            return False

        if os.path.isfile(filename):
            response = gtkutil.dialog( self.main_window, _('File already exists'),
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
        if not self.playlist.save_to_new_playlist(filename, ext):
            self.notify(_('Error saving playlist...'))
            return False

        return True

    def empty_playlist_callback(self, w):
        self.playlist.reset_playlist()
        self.__playlist_tab.treeview.get_model().clear()

    def delete_all_bookmarks_callback(self, widget=None):
        response = gtkutil.dialog(
                self.main_window, _('Delete All Bookmarks'),
                _('Would you like to delete all bookmarks?'),
                _('By accepting all bookmarks in the database will be deleted.'),
                negative_button=None)

        self.__log.debug('Response to "Delete all bookmarks?": %s', response)

        if response:
            self.playlist.delete_all_bookmarks()
            model = self.__playlist_tab.treeview.get_model()

            for row in iter(model):
                while model.iter_has_child(row.iter):
                    bkmk_iter = model.iter_children(row.iter)
                    model.remove(bkmk_iter)

    def set_boolean_config_callback(self, w):
        if w.get_active():
            self.config.set("options", w.get_name(), "true")
        else:
            self.config.set("options", w.get_name(), "false")

    def scrolling_labels_callback(self, w):
        self.set_boolean_config_callback(w)
        self.__player_tab.title_label.scrolling = w.get_active()

    def set_play_mode_callback(self, w):
        self.config.set("options", "play_mode", w.get_name())

    def __get_fullscreen(self):
        return self.__window_fullscreen

    def __set_fullscreen(self, value):
        if value != self.__window_fullscreen:
            if value:
                self.main_window.fullscreen()
            else:
                self.main_window.unfullscreen()

            self.__window_fullscreen = value
            self.playlist.send_metadata()

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

    def settings_callback(self, widget):
        from panucci.gtkui.gtksettingsdialog import SettingsDialog
        SettingsDialog(self)

    def about_callback(self, widget):
        if platform.FREMANTLE:
            from panucci.gtkui.gtkaboutdialog import HeAboutDialog
            HeAboutDialog.present(self.main_window, panucci.__version__)
        else:
            from panucci.gtkui.gtkaboutdialog import AboutDialog
            AboutDialog(self.main_window, panucci.__version__)

    def show_fm_transmitter(self, ws):
        import osso
        ctx = osso.Context('Panucci', '1.3.3.7', False)
        plugin = osso.Plugin(ctx)
        plugin.plugin_execute('libcpfmtx.so', True)

    def _play_file(self, filename, pause_on_load=False):
        self.playlist.load( os.path.abspath(filename) )

        if self.playlist.is_empty:
            return False

    def handle_headset_button(self, event, button):
        if event == 'ButtonPressed' and button == 'phone':
            self.playlist.player.play_pause_toggle()

    def handle_connection_state(self, device_path):
        PATH = '/org/freedesktop/Hal/devices/computer_logicaldev_input_1'
        if device_path == PATH and self.config.getboolean("options", "play_on_headset") and not self.playlist.player.playing:
            self.playlist.player.play()

    def handle_bt_button(self, signal, button):
        # See http://bugs.maemo.org/8283 for details
        if signal == 'ButtonPressed':
            if button == 'play-cd':
                self.playlist.player.play_pause_toggle()
            elif button == 'pause-cd':
                self.playlist.player.pause()
            elif button == 'next-song':
                self.__player_tab.do_seek(self.config.getint("options", "seek_short"))
            elif button == 'previous-song':
                self.__player_tab.do_seek(-1*self.config.getint("options", "seek_short"))

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
        self.config = gui_root.config
        self.playlist = gui_root.playlist

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

        self.playlist.player.register( 'stopped', self.on_player_stopped )
        self.playlist.player.register( 'playing', self.on_player_playing )
        self.playlist.player.register( 'paused', self.on_player_paused )
        #self.playlist.player.register( 'eof', self.on_player_eof )
        self.playlist.register( 'end-of-playlist',
                                  self.on_player_end_of_playlist )
        self.playlist.register( 'new-track-loaded',
                                  self.on_player_new_track )
        self.playlist.register( 'new-metadata-available',
                                  self.on_player_new_metadata )
        self.playlist.register( 'reset-playlist',
                                  self.on_player_reset_playlist )

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
        separator = gtk.Label("")
        separator.set_size_request(-1, 10)
        metadata_vbox.pack_start(separator, False, False)
        self.album_label = gtk.Label('')
        if platform.FREMANTLE:
            hildon.hildon_helper_set_logical_font(self.album_label, 'SmallSystemFont')
            hildon.hildon_helper_set_logical_color(self.album_label, gtk.RC_FG, gtk.STATE_NORMAL, 'SecondaryTextColor')
        else:
            self.album_label.modify_font(pango.FontDescription('normal 8'))
        self.album_label.set_ellipsize(pango.ELLIPSIZE_END)
        metadata_vbox.pack_start(self.album_label, False, False)
        separator = gtk.Label("")
        separator.set_size_request(-1, 10)
        metadata_vbox.pack_start(separator, False, False)
        self.title_label = widgets.ScrollingLabel('',
                                                  self.config.get("options", "scrolling_color"),
                                                  update_interval=100,
                                                  pixel_jump=1,
                                                  delay_btwn_scrolls=5000,
                                                  delay_halfway=3000)
        self.title_label.scrolling = self.config.getboolean("options", "scrolling_labels")
        metadata_vbox.pack_start(self.title_label, False, False)
        metadata_vbox.pack_start(gtk.Image(), True, True)
        metadata_hbox.pack_start( metadata_vbox, True, True )

        progress_eventbox = gtk.EventBox()
        progress_eventbox.set_events(gtk.gdk.BUTTON_PRESS_MASK)
        progress_eventbox.connect(
            'button-press-event', self.on_progressbar_changed )
        self.progress = gtk.ProgressBar()
        self.progress.set_size_request(-1, self.config.getint("options", "progress_height"))
        progress_eventbox.add(self.progress)
        main_vbox.pack_start( progress_eventbox, False, False )

        # make the button box
        buttonbox = gtk.HBox()

        # A wrapper to help create DualActionButtons with the right settings
        def create_da(widget, action, widget2=None, action2=None):
            if platform.FREMANTLE:
                widget2 = None
                action2 = None

            return widgets.DualActionButton(widget, action, self.config, widget2, action2)

        self.rrewind_button = create_da(
                gtkutil.generate_image('media-skip-backward.png'),
                lambda: self.do_seek(-1*self.config.getint('options', 'seek_long')),
                gtkutil.generate_image("gtk-goto-first-ltr.png"),
                self.playlist.prev)
        buttonbox.add(self.rrewind_button)

        self.rewind_button = create_da(
                gtkutil.generate_image('media-seek-backward.png'),
                lambda: self.do_seek(-1*self.config.getint('options', 'seek_short')))
        buttonbox.add(self.rewind_button)

        self.play_pause_button = gtk.Button('')
        gtkutil.image(self.play_pause_button, 'media-playback-start.png')
        self.play_pause_button.connect( 'clicked',
                                        self.on_btn_play_pause_clicked )
        self.play_pause_button.set_sensitive(False)
        buttonbox.add(self.play_pause_button)

        self.forward_button = create_da(
                gtkutil.generate_image('media-seek-forward.png'),
                lambda: self.do_seek(self.config.getint('options', 'seek_short')))
        buttonbox.add(self.forward_button)

        self.fforward_button = create_da(
                gtkutil.generate_image('media-skip-forward.png'),
                lambda: self.do_seek(self.config.getint('options', 'seek_long')),
                gtkutil.generate_image("gtk-goto-last-ltr.png"),
                self.playlist.next)
        buttonbox.add(self.fforward_button)

        self.bookmarks_button = create_da(
                gtkutil.generate_image('bookmark-new.png'),
                self.playlist.player.add_bookmark_at_current_position,
                gtkutil.generate_image(gtk.STOCK_JUMP_TO, True),
                lambda *args: self.notify('select-current-item-request'))
        buttonbox.add(self.bookmarks_button)
        self.set_controls_sensitivity(False)

        if platform.FREMANTLE:
            for child in buttonbox.get_children():
                if isinstance(child, gtk.Button):
                    child.set_name('HildonButton-thumb')

        buttonbox.set_size_request(-1, self.config.getint("options", "button_height"))
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

            button.set_longpress_enabled( self.config.getboolean("options", "dual_action_button") )
            button.set_duration( self.config.getfloat("options", "dual_action_button_delay") )

    def on_key_press(self, widget, event):
        if platform.MAEMO:
            if event.keyval == gtk.keysyms.Left: # seek back
                self.do_seek( -1 * self.config.getint('options', 'seek_long') )
            elif event.keyval == gtk.keysyms.Right: # seek forward
                self.do_seek( self.config.getint('options', 'seek_long') )
            elif event.keyval == gtk.keysyms.Return: # play/pause
                self.on_btn_play_pause_clicked()

    def on_player_stopped(self):
        self.stop_progress_timer()
        self.set_controls_sensitivity(False)
        gtkutil.image(self.play_pause_button, 'media-playback-start.png')

    def on_player_playing(self):
        self.start_progress_timer()
        gtkutil.image(self.play_pause_button, 'media-playback-pause.png')
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
        self.metadata = self.playlist.get_file_metadata()
        self.set_metadata(self.metadata)

        if not self.playlist.player.playing:
            position = self.playlist.get_current_position()
            estimated_length = self.metadata.get('length', 0)
            self.set_progress_callback( position, estimated_length )
            self.playlist.player.set_position_duration(position, 0)

    def on_player_paused( self, position, duration ):
        self.stop_progress_timer() # This should save some power
        self.set_progress_callback( position, duration )
        gtkutil.image(self.play_pause_button, 'media-playback-start.png')

    def on_player_end_of_playlist(self, loop):
        if not loop:
            self.playlist.player.stop_end_of_playlist()
            estimated_length = self.metadata.get('length', 0)
            self.set_progress_callback( 0, estimated_length )
            self.playlist.player.set_position_duration(0, 0)

    def on_player_reset_playlist(self):
        self.on_player_stopped()
        self.on_player_new_track()
        self.reset_progress()

    def reset_progress(self):
        self.progress.set_fraction(0)
        self.set_progress_callback(0,0)
        self.__gui_root.main_window.set_title("Panucci")

    def set_progress_callback(self, time_elapsed, total_time):
        """ times must be in nanoseconds """
        time_string = "%s / %s" % ( util.convert_ns(time_elapsed),
            util.convert_ns(total_time) )
        self.progress.set_text( time_string )
        fraction = float(time_elapsed) / float(total_time) if total_time else 0
        self.progress.set_fraction( fraction )

    def on_progressbar_changed(self, widget, event):
        if ( not self.config.getboolean("options", "lock_progress") and
                event.type == gtk.gdk.BUTTON_PRESS and event.button == 1 ):
            new_fraction = event.x/float(widget.get_allocation().width)
            resp = self.playlist.player.do_seek(percent=new_fraction)
            if resp:
                # Preemptively update the progressbar to make seeking smoother
                self.set_progress_callback( *resp )

    def on_btn_play_pause_clicked(self, widget=None):
        self.playlist.player.play_pause_toggle()

    def progress_timer_callback( self ):
        if self.playlist.player.playing and not self.playlist.player.seeking:
            pos_int, dur_int = self.playlist.player.get_position_duration()
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
                size = util.coverart_sizes['maemo fullscreen']
            else:
                size = util.coverart_sizes['maemo']
        else:
            size = util.coverart_sizes['normal']

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
                pixbuf = pbl.get_pixbuf()
                pixbuf = pixbuf.scale_simple(self.config.getint("options", "cover_height"),
                    self.config.getint("options", "cover_height"), gtk.gdk.INTERP_BILINEAR )
                self.set_coverart(pixbuf)
            except Exception, e:
                self.__log.exception('Error setting coverart...')

        # set the text metadata
        for tag,value in tag_message.iteritems():
            if tags.has_key(tag) and value is not None and value.strip():
                if tag == "artist":
                    _str = '<big>' + cgi.escape(value) + '</big>'
                elif tag == "album":
                    _str = cgi.escape(value)
                elif tag == "title":
                    _str = '<b><big>' + cgi.escape(value) + '</big></b>'
                    if not platform.MAEMO:
                        value += ' - Panucci'
                    if platform.FREMANTLE and len(value) > 25:
                        value = value[:24] + '...'
                    self.__gui_root.main_window.set_title( value )
                
                try:
                    tags[tag].set_markup(_str)
                except TypeError, e:
                    self.__log.exception(str(e))
                tags[tag].set_alignment( 0.5*int(not self.has_coverart), 0.5)
                tags[tag].show()

    def do_seek(self, seek_amount):
        resp = self.playlist.do_seek(seek_amount*10**9)
        if resp:
            # Preemptively update the progressbar to make seeking smoother
            self.set_progress_callback( *resp )
