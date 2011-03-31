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
from PySide  import QtCore
from PySide import QtGui

try:
    import pynotify
    pynotify.init('Panucci')
    have_pynotify = True
except:
    have_pynotify = False

import panucci
from panucci import util
from panucci import platform
from panucci import playlist
from panucci.dbusinterface import interface
from panucci.services import ObservableService
from panucci.qtui import qtutil
from panucci.qtui import qtplaylist
from panucci.qtui import qtwidgets

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

        self.app = QtGui.QApplication(["Panucci"])
        self.app.setWindowIcon(QtGui.QIcon(util.find_data_file('panucci.png')))
        self.main_window = QtGui.QMainWindow(None)
        if platform.FREMANTLE:
            self.main_window.setAttribute(QtCore.Qt.WA_Maemo5StackedWindow)
        self.main_window.closeEvent = self.close_main_window_callback
        self.create_actions()
        self.__player_tab = PlayerTab(self)
        self.__playlist_tab = qtplaylist.PlaylistTab(self, self.playlist)
        if platform.MAEMO:
            self.create_maemo_menus()
        else:
            self.create_menus()
        widget = QtGui.QWidget()
        widget.setLayout(self.__player_tab.mainbox)
        self.main_window.setCentralWidget(widget)
        self.main_window.show()
        self.playlist.init(filepath=filename)
        self.app.exec_()

    def create_actions(self):
        # File menu
        self.action_add_file = QtGui.QAction(QtGui.QIcon(':/actions/add.png'), _("Add File").decode("utf-8"), self.main_window, shortcut="Ctrl+A",
            statusTip="Add file to playlist", triggered=self.add_file_callback)
        self.action_add_folder = QtGui.QAction(QtGui.QIcon(':/images/open.png'), _("Add Folder").decode("utf-8"), self.main_window, shortcut="Ctrl+D",
            statusTip="Add folder to playlist", triggered=self.add_folder_callback)
        self.action_save_playlist = QtGui.QAction(QtGui.QIcon(':/images/save.png'), _("Save Playlist").decode("utf-8"), self.main_window, shortcut="Ctrl+W",
            statusTip="Save current playlist as m3u", triggered=self.save_playlist_callback)
        self.action_clear_playlist = QtGui.QAction(QtGui.QIcon(':/images/trashcan.png'), _("Clear Playlist").decode("utf-8"), self.main_window, shortcut="Ctrl+H",
            statusTip="Clear current playlist", triggered=self.clear_playlist_callback)
        self.action_delete_bookmarks = QtGui.QAction(QtGui.QIcon(':/images/trashcan.png'), _("Delete All Bookmarks").decode("utf-8"), self.main_window, shortcut="Ctrl+K",
            statusTip="Delete all bookmarks", triggered=self.delete_bookmarks_callback)
        self.action_quit = QtGui.QAction(QtGui.QIcon('/usr/share/icons/gnome/16x16/actions/exit.png'), "Quit", self.main_window, shortcut="Ctrl+Q",
            statusTip="Exit the application", triggered=self.quit_panucci)
        # Tools menu
        self.action_playlist = QtGui.QAction("Playlist", self.main_window, shortcut="Ctrl+P",
            statusTip="Open playlist", triggered=self.playlist_callback)
        self.action_settings = QtGui.QAction("Settings", self.main_window, shortcut="Ctrl+C",
            statusTip="Open settings dialog", triggered=self.settings_callback)
        self.action_timer = QtGui.QAction("Sleep Timer", self.main_window, shortcut="Ctrl+T",
            statusTip="Start a timed shutdown", triggered=self.create_timer_dialog)
        # Settings menu
        self.action_lock_progress = QtGui.QAction(_("Lock Progress Bar").decode("utf-8"), self.main_window, shortcut="Ctrl+L",
            statusTip="Lock progress bar", triggered=self.lock_progress_callback)
        self.action_lock_progress.setCheckable(True)
        self.action_lock_progress.setChecked(self.config.getboolean("options", "lock_progress"))
        self.action_dual_action = QtGui.QAction(_("Dual Action Button").decode("utf-8"), self.main_window, shortcut="Ctrl+B",
            statusTip="Set dual action button", triggered=self.dual_action_callback)
        self.action_dual_action.setCheckable(True)
        self.action_dual_action.setChecked(self.config.getboolean("options", "dual_action_button"))
        self.action_stay_at_end = QtGui.QAction(_("Stay at End").decode("utf-8"), self.main_window, shortcut="Ctrl+E",
            statusTip="Stay at file end", triggered=self.stay_at_end_callback)
        self.action_stay_at_end.setCheckable(True)
        self.action_stay_at_end.setChecked(self.config.getboolean("options", "stay_at_end"))
        self.action_seek_back = QtGui.QAction(_("Seek Back").decode("utf-8"), self.main_window, shortcut="Ctrl+S",
            statusTip="Seek back to previous file", triggered=self.seek_back_callback)
        self.action_seek_back.setCheckable(True)
        self.action_seek_back.setChecked(self.config.getboolean("options", "seek_back"))
        self.action_scrolling_labels = QtGui.QAction(_("Scrolling Labels").decode("utf-8"), self.main_window, shortcut="Ctrl+V",
            statusTip="Scroll title labels when too long", triggered=self.scrolling_labels_callback)
        self.action_scrolling_labels.setCheckable(True)
        self.action_scrolling_labels.setChecked(self.config.getboolean("options", "scrolling_labels"))
        self.action_play_mode_all = QtGui.QAction(_("All").decode("utf-8"), self.main_window, statusTip="Set play mode",
            triggered=self.play_mode_all_callback)
        self.action_play_mode_all.setCheckable(True)
        self.action_play_mode_single = QtGui.QAction(_("Single").decode("utf-8"), self.main_window, statusTip="Set play mode",
            triggered=self.play_mode_single_callback)
        self.action_play_mode_single.setCheckable(True)
        self.action_play_mode_random = QtGui.QAction(_("Random").decode("utf-8"), self.main_window, statusTip="Set play mode",
            triggered=self.play_mode_random_callback)
        self.action_play_mode_random.setCheckable(True)
        self.action_play_mode_repeat = QtGui.QAction(_("Repeat").decode("utf-8"), self.main_window, statusTip="Set play mode",
            triggered=self.play_mode_repeat_callback)
        self.action_play_mode_repeat.setCheckable(True)
        actiongroup = QtGui.QActionGroup(self.main_window)
        actiongroup.setExclusive(True)
        self.action_play_mode_all.setActionGroup(actiongroup)
        self.action_play_mode_single.setActionGroup(actiongroup)
        self.action_play_mode_random.setActionGroup(actiongroup)
        self.action_play_mode_repeat.setActionGroup(actiongroup)
        if self.config.get("options", "play_mode") == "single":
            self.action_play_mode_single.setChecked(True)
        elif self.config.get("options", "play_mode") == "random":
            self.action_play_mode_random.setChecked(True)
        elif self.config.get("options", "play_mode") == "repeat":
            self.action_play_mode_repeat.setChecked(True)
        else:
            self.action_play_mode_all.setChecked(True)
        # help menu
        self.action_about = QtGui.QAction(QtGui.QIcon('about.png'), _("About").decode("utf-8"), self.main_window,
            statusTip="Show about dialog", triggered=self.about_callback)

    def create_menus(self):
        # File menu
        self.menu_file = self.main_window.menuBar().addMenu(_("File").decode("utf-8"))
        self.menu_file.addAction(self.action_add_file)
        self.menu_file.addAction(self.action_add_folder)
        self.menu_file.addAction(self.action_save_playlist)
        self.menu_file.addAction(self.action_clear_playlist)
        self.menu_file.addAction(self.action_delete_bookmarks)
        self.menu_file.addSeparator()
        self.menu_file.addAction(self.action_quit)
        # Tools menu
        self.menu_tools = self.main_window.menuBar().addMenu(_("Tools").decode("utf-8"))
        self.menu_tools.addAction(self.action_playlist)
        self.menu_tools.addAction(self.action_timer)
        self.menu_tools.addAction(self.action_settings)
        # Settings menu
        self.menu_settings = self.main_window.menuBar().addMenu(_("Settings").decode("utf-8"))
        self.menu_settings.addAction(self.action_lock_progress)
        self.menu_settings.addAction(self.action_dual_action)
        self.menu_settings.addAction(self.action_stay_at_end)
        self.menu_settings.addAction(self.action_seek_back)
        self.menu_settings.addAction(self.action_scrolling_labels)
        self.menu_play_mode = self.menu_settings.addMenu(_("Play Mode").decode("utf-8"))
        self.menu_play_mode.addAction(self.action_play_mode_all)
        self.menu_play_mode.addAction(self.action_play_mode_single)
        self.menu_play_mode.addAction(self.action_play_mode_random)
        self.menu_play_mode.addAction(self.action_play_mode_repeat)
        # Help menu
        self.menu_help = self.main_window.menuBar().addMenu(_("Help").decode("utf-8"))
        self.menu_help.addAction(self.action_about)

    def create_maemo_menus(self):
        # Player menu
        self.menu_player = self.main_window.menuBar().addMenu("Player")
        self.menu_player.addAction(self.action_settings)
        self.menu_player.addAction(self.action_playlist)
        self.menu_player.addAction(self.action_add_file)
        self.menu_player.addAction(self.action_add_folder)
        self.menu_player.addAction(self.action_clear_playlist)
        self.menu_player.addAction(self.action_timer)
        self.menu_player.addAction(self.action_about)
        # Playlist menu
        self.menu_playlist = self.__playlist_tab.main_window.menuBar().addMenu("Playlist")
        self.menu_playlist.addAction(self.action_save_playlist)
        self.menu_playlist.addAction(self.action_delete_bookmarks)
 
    def create_timer_dialog(self):
        response = QtGui.QInputDialog.getInteger(self.main_window, "Sleep Timer", "Shutdown time in minutes",
                       value=5, minValue=1)
        if response[1]:
            QtCore.QTimer.singleShot(60000*response[0], self.quit_panucci)

    def quit_panucci(self):
        self.main_window.hide()
        self.playlist.quit()
        util.write_config(self.config)
        self.app.exit()

    def close_main_window_callback(self, event):
        self.quit_panucci()

    def show_main_window(self):
        self.main_window.activateWindow()

    def add_file_callback(self):
        filenames = qtutil.get_file_from_filechooser(self)
        if filenames:
            self._play_file(filenames[0].encode('utf-8'))

    def add_folder_callback(self):
        filenames = qtutil.get_file_from_filechooser(self, folder=True)
        if filenames:
            self._play_file(filenames[0].encode('utf-8'))

    def save_playlist_callback(self):
        filenames = qtutil.get_file_from_filechooser(self, save_file=True, save_to=True)
        if not filenames:
            return False

        filename = filenames[0]
        if os.path.isfile(filename):
            response = qtutil.dialog(self.main_window,  _('File already exists!'),
                _('The file %s already exists. You can choose another name or '
                  'overwrite the existing file.') % os.path.basename(filename), False, True, True, True)

            if response == QtGui.QMessageBox.Cancel:
                return None
            elif response == QtGui.QMessageBox.Discard:
                return self.save_playlist_callback()

        ext = util.detect_filetype(filename)
        if not self.playlist.save_to_new_playlist(filename, ext):
            self.notify(_('Error saving playlist...'))
            return False

        return True

    def clear_playlist_callback(self):
        self.playlist.reset_playlist()
        self.__playlist_tab.clear_model()

    def delete_bookmarks_callback(self):
        response = qtutil.dialog(self.main_window,  _('Delete all bookmarks?'),
                _('By accepting all bookmarks in the database will be deleted.'), True, False, True, False)
        if response == QtGui.QMessageBox.Ok:
            self.playlist.delete_all_bookmarks()

    def playlist_callback(self):
        self.__playlist_tab.main_window.show()

    def settings_callback(self):
        from panucci.qtui.qtsettingsdialog import SettingsDialog
        SettingsDialog(self)

    def lock_progress_callback(self):
        self.set_config_option("lock_progress", str(self.action_lock_progress.isChecked()).lower())

    def dual_action_callback(self):
        self.set_config_option("dual_action_button", str(self.action_dual_action.isChecked()).lower())

    def stay_at_end_callback(self):
        self.set_config_option("stay_at_end", str(self.action_stay_at_end.isChecked()).lower())

    def seek_back_callback(self):
        self.set_config_option("seek_back", str(self.action_seek_back.isChecked()).lower())

    def scrolling_labels_callback(self):
        self.set_config_option("scrolling_labels", str(self.action_scrolling_labels.isChecked()).lower())
        self.__player_tab.label_title.set_scrolling(self.config.getboolean("options", "scrolling_labels"))

    def play_mode_all_callback(self):
        self.set_config_option("play_mode", "all")

    def play_mode_single_callback(self):
        self.set_config_option("play_mode", "single")

    def play_mode_random_callback(self):
        self.set_config_option("play_mode", "random")

    def play_mode_repeat_callback(self):
        self.set_config_option("play_mode", "repeat")

    def about_callback(self):
        from panucci.qtui import qtaboutdialog
        qtaboutdialog.AboutDialog(self.main_window, panucci.__version__)

    def set_config_option(self, option, value):
        self.config.set("options", option, value)

    def _play_file(self, filename, pause_on_load=False):
        self.playlist.load( os.path.abspath(filename) )

        if self.playlist.is_empty:
            return False

##################################################
# PlayerTab
##################################################
class PlayerTab(ObservableService):
    """ The tab that holds the player elements """

    signals = [ 'select-current-item-request', ]

    def __init__(self, gui_root):
        self.__log = logging.getLogger('panucci.panucci.PlayerTab')
        self.__gui_root = gui_root
        self.config = gui_root.config
        self.playlist = gui_root.playlist
        ObservableService.__init__(self, self.signals, self.__log)

        self.playlist.player.register( 'stopped', self.on_player_stopped )
        self.playlist.player.register( 'playing', self.on_player_playing )
        self.playlist.player.register( 'paused', self.on_player_paused )
        #self.playlist.player.register( 'eof', self.on_player_eof )
        self.playlist.register( 'end-of-playlist', self.on_player_end_of_playlist )
        self.playlist.register( 'new-track-loaded', self.on_player_new_track )
        self.playlist.register( 'new-metadata-available', self.on_player_new_metadata )
        self.playlist.register( 'reset-playlist', self.on_player_reset_playlist )

        self.mainbox = QtGui.QVBoxLayout()
        self.mainbox.setContentsMargins(0, 0, 0, 0)
        self.mainbox.setSpacing(0)

        layout = QtGui.QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self.label_cover = QtGui.QLabel()
        self.label_cover.setContentsMargins(0, 5, 2, 5)
        layout.addWidget(self.label_cover)
        vlayout = QtGui.QVBoxLayout()
        vlayout.setContentsMargins(0, 0, 0, 0)
        vlayout.setSpacing(0)
        vlayout.addStretch(5)
        self.label_artist = QtGui.QLabel()
        self.label_album = QtGui.QLabel()
        self.label_artist.setContentsMargins(3, 0, 5, 10)
        self.label_album.setContentsMargins(3, 0, 5, 10)
        self.label_title = qtwidgets.ScrollingLabel(self.config)
        self.label_title.setContentsMargins(0, 0, 0, 0)
        vlayout.addWidget(self.label_artist)
        vlayout.addWidget(self.label_album)
        vlayout.addWidget(self.label_title)
        vlayout.addStretch(5)
        layout.addLayout(vlayout, 2)
        self.mainbox.addLayout(layout, 8)

        self.progress = QtGui.QProgressBar()
        self.progress.setContentsMargins(0, 0, 0, 0)
        self.mainbox.addWidget(self.progress)
        self.progress.setTextVisible(True)
        self.progress.setFormat("00:00 / 00:00")
        self.progress.setValue(0)
        self.progress.mousePressEvent = self.on_progress_clicked
        self.progress.setFixedHeight(self.config.getint("options", "progress_height"))

        self.icon_play = QtGui.QIcon(util.find_data_file('media-playback-start.png'))
        self.icon_pause = QtGui.QIcon(util.find_data_file('media-playback-pause.png'))
        self.button_rrewind = qtwidgets.DualActionButton(self.config,
                                                      QtGui.QIcon(util.find_data_file('media-skip-backward.png')),
                                                      self.button_rrewind_callback,
                                         QtGui.QIcon("/usr/share/icons/gnome/24x24/actions/gtk-goto-first-ltr.png"),
                                         self.playlist.prev)
        self.button_rrewind.setFixedHeight(self.config.getint("options", "button_height"))
        self.button_rewind = QtGui.QPushButton(QtGui.QIcon(util.find_data_file('media-seek-backward.png')), "")
        self.button_rewind.clicked.connect(self.button_rewind_callback)
        self.button_rewind.setFixedHeight(self.config.getint("options", "button_height"))
        self.button_play = QtGui.QPushButton(self.icon_play, "")
        self.button_play.clicked.connect(self.button_play_callback)
        self.button_play.setFixedHeight(self.config.getint("options", "button_height"))
        self.button_forward = QtGui.QPushButton(QtGui.QIcon(util.find_data_file('media-seek-forward.png')), "")
        self.button_forward.clicked.connect(self.button_forward_callback)
        self.button_forward.setFixedHeight(self.config.getint("options", "button_height"))
        self.button_fforward = qtwidgets.DualActionButton(self.config,
                                                      QtGui.QIcon(util.find_data_file('media-skip-forward.png')),
                                                      self.button_fforward_callback,
                                         QtGui.QIcon("/usr/share/icons/gnome/24x24/actions/gtk-goto-last-ltr.png"),
                                         self.playlist.next)
        self.button_fforward.setFixedHeight(self.config.getint("options", "button_height"))
        self.button_bookmark = QtGui.QPushButton(QtGui.QIcon(util.find_data_file('bookmark-new.png')), "")
        self.button_bookmark.clicked.connect(self.button_bookmark_callback)
        self.button_bookmark.setFixedHeight(self.config.getint("options", "button_height"))

        layout = QtGui.QHBoxLayout()
        layout.setContentsMargins(0, 4, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self.button_rrewind)
        layout.addWidget(self.button_rewind)
        layout.addWidget(self.button_play)
        layout.addWidget(self.button_forward)
        layout.addWidget(self.button_fforward)
        layout.addWidget(self.button_bookmark)
        self.mainbox.addLayout(layout)

        self.timer = QtCore.QTimer()
        self.timer.setInterval(1000); 
        self.timer.timeout.connect(self.timer_callback)

    def on_player_stopped(self):
        self.stop_progress_timer()
        #self.set_controls_sensitivity(False)
        self.button_play.setIcon(self.icon_play)

    def on_player_playing(self):
        self.start_progress_timer()
        self.button_play.setIcon(self.icon_pause)
        #self.set_controls_sensitivity(True)

    def on_player_paused( self, position, duration ):
        self.stop_progress_timer()
        #self.set_progress_callback( position, duration )
        self.button_play.setIcon(self.icon_play)

    def on_player_new_track(self):
        for widget in [self.label_title, self.label_artist, self.label_album, self.label_cover]:
            widget.setText('')
        self.label_cover.hide()
        self.has_coverart = False

    def on_player_new_metadata(self):
        self.metadata = self.playlist.get_file_metadata()
        self.set_metadata(self.metadata)
        
        if not self.playlist.player.playing:
            position = self.playlist.get_current_position()
            estimated_length = self.metadata.get('length', 0)
            self.set_progress_callback( position, estimated_length )
            self.playlist.player.set_position_duration(position, 0)

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
        self.__gui_root.main_window.setWindowTitle("Panucci")

    def reset_progress(self):
        self.set_progress_callback(0,0)

    def button_rrewind_callback(self):
         self.do_seek(-1*self.config.getint("options", "seek_long"))

    def button_rewind_callback(self):
        self.do_seek(-1*self.config.getint("options", "seek_short"))

    def button_play_callback(self):
        self.playlist.player.play_pause_toggle()

    def button_forward_callback(self):
        self.do_seek(self.config.getint("options", "seek_short"))

    def button_fforward_callback(self):
         self.do_seek(self.config.getint("options", "seek_long"))

    def button_bookmark_callback(self):
        self.playlist.player.add_bookmark_at_current_position()

    def set_progress_callback(self, time_elapsed, total_time):
        """ times must be in nanoseconds """
        time_string = "%s / %s" % ( util.convert_ns(time_elapsed),
            util.convert_ns(total_time) )
        self.progress.setFormat( time_string )
        fraction = float(time_elapsed) / float(total_time) if total_time else 0
        self.progress.setValue( int(fraction*100) )

    def on_progress_clicked(self, event):
        if ( not self.config.getboolean("options", "lock_progress") and
                event.button() == QtCore.Qt.MouseButton.LeftButton ):
            new_fraction = float(event.x())/float(self.progress.width())
            resp = self.playlist.player.do_seek(percent=new_fraction)
            if resp:
                # Preemptively update the progressbar to make seeking smoother
                self.set_progress_callback( *resp )

    def timer_callback( self ):
        if self.playlist.player.playing and not self.playlist.player.seeking:
            pos_int, dur_int = self.playlist.player.get_position_duration()
            # This prevents bogus values from being set while seeking
            if ( pos_int > 10**9 ) and ( dur_int > 10**9 ):
                self.set_progress_callback( pos_int, dur_int )
        return True

    def start_progress_timer( self ):
        self.timer.start()
        
    def stop_progress_timer( self ):
        self.timer.stop()

    def get_cover_size(self):
        if self.__gui_root.main_window.isFullScreen():
            size = self.config.getint("options", "cover_full_height")
        else:
            size = self.config.getint("options", "cover_height")
        return size

    def set_cover_size(self):
        if self.has_coverart:
            size = self.get_cover_size()
            pixmap = self.label_cover.pixmap().scaled(size, size, mode=QtCore.Qt.SmoothTransformation)
            self.label_cover.setPixmap(pixmap)

    def set_metadata( self, tag_message ):
        tags = { 'title': self.label_title, 'artist': self.label_artist,
                 'album': self.label_album }

        # set the coverart
        if tag_message.has_key('image') and tag_message['image'] is not None:
            value = tag_message['image']

            try:
                pixmap = QtGui.QPixmap()
                pixmap.loadFromData(value)
                size = self.get_cover_size()
                pixmap = pixmap.scaled(size, size, mode=QtCore.Qt.SmoothTransformation)
                self.label_cover.setPixmap(pixmap)
                self.label_cover.show()
                self.has_coverart = True
            except Exception, e:
                self.__log.exception('Error setting coverart...')

        # set the text metadata
        for tag,value in tag_message.iteritems():
            if tags.has_key(tag) and value is not None and value.strip():
                value = value.decode('utf-8')
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
                    self.__gui_root.main_window.setWindowTitle(value)
 
                if not self.has_coverart:
                    tags[tag].setAlignment(QtCore.Qt.AlignHCenter)
                else:
                    tags[tag].setAlignment(QtCore.Qt.AlignLeft)
                try:
                    tags[tag].setText(_str)
                except TypeError, e:
                    self.__log.exception(str(e))
                
                tags[tag].show()

    def do_seek(self, seek_amount):
        seek_amount = seek_amount*10**9
        resp = None
        if not self.config.getboolean("options", "seek_back") or self.playlist.start_of_playlist() or seek_amount > 0:
            resp = self.playlist.player.do_seek(from_current=seek_amount)
        else:
            pos_int, dur_int = self.playlist.player.get_position_duration()
            if pos_int + seek_amount >= 0:
                resp = self.playlist.player.do_seek(from_current=seek_amount)
            else:
                self.playlist.prev()
                pos_int, dur_int = self.playlist.player.get_position_duration()
                resp = self.playlist.player.do_seek(from_beginning=dur_int+seek_amount)
        if resp:
            # Preemptively update the progressbar to make seeking smoother
            self.set_progress_callback( *resp )
