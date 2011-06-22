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

import sys
import os
import logging
import ConfigParser

from PySide import QtCore
from PySide import QtGui
from PySide import QtDeclarative

import panucci
from panucci import util
from panucci import platform
from panucci import playlist
from panucci.dbusinterface import interface
from panucci.services import ObservableService

class PanucciGUI(QtCore.QObject, ObservableService):
    def __init__(self, settings, filename=None):
        self.__log = logging.getLogger('panucci.panucci.PanucciGUI')
        QtCore.QObject.__init__(self)
        ObservableService.__init__(self, [], self.__log)
        self.config = settings.config
        interface.register_gui(self)
        self.playlist = playlist.Playlist(self.config)
        self.time_str = "00:00 / 00:00"
        self.progress_fraction = 0
        self.metadata = None

        self.app = QtGui.QApplication(["Panucci"])
        self.app.setWindowIcon(QtGui.QIcon(util.find_data_file('panucci.png')))
        self.main_window = QtGui.QMainWindow(None)
        self.main_window.closeEvent = self.close_main_window_callback
        self.view = QtDeclarative.QDeclarativeView(self.main_window)
        self.context = self.view.rootContext()
        self.context.setContextProperty('main', self)
        self.context.setContextProperty('config', self.make_config())
        self.theme_controller = ThemeController(self.config)
        self.context.setContextProperty('themeController', self.theme_controller)
        self.create_actions()
        engine = self.context.engine()
        self.image_provider = ImageProvider(self)
        engine.addImageProvider("cover", self.image_provider)
        self.view.setSource(util.find_data_file("main.qml"))

        self.playlist.register( 'stopped', self.on_player_stopped )
        self.playlist.register( 'playing', self.on_player_playing )
        self.playlist.register( 'paused', self.on_player_paused )
        self.playlist.register( 'end-of-playlist', self.on_player_end_of_playlist )
        self.playlist.register( 'new-track-loaded', self.on_player_new_track )
        self.playlist.register( 'new-metadata-available', self.on_player_new_metadata )
        self.playlist.register( 'reset-playlist', self.on_player_reset_playlist )

        self.playlist.init(filepath=filename)
        self.view.rootObject().start_scrolling_timer(self.config.getboolean("options", "scrolling_labels"))
        self.timer = QtCore.QTimer()
        self.timer.setInterval(1000)
        self.timer.timeout.connect(self.timer_callback)
        self.main_window.setCentralWidget(self.view)
        self.main_window.show()
        self.app.exec_()

    def create_actions(self):
        # File menu
        self.action_add_media = QtGui.QAction(QtGui.QIcon(''), _("Add Media").decode("utf-8"), self.main_window, shortcut="Ctrl+A",
            statusTip="Add file to playlist", triggered=self.add_media_callback)
        self.context.setContextProperty('action_add_media', self.action_add_media)
        self.action_play_one = QtGui.QAction(QtGui.QIcon(''), _("Play One").decode("utf-8"), self.main_window, shortcut="Ctrl+O",
            statusTip="Play one file", triggered=self.play_one_callback)
        self.context.setContextProperty('action_play_one', self.action_play_one)
        self.action_save_playlist = QtGui.QAction(QtGui.QIcon(':/images/save.png'), _("Save Playlist").decode("utf-8"), self.main_window, shortcut="Ctrl+W",
            statusTip="Save current playlist as m3u", triggered=self.save_playlist_callback)
        self.context.setContextProperty('action_save_playlist', self.action_save_playlist)
        self.action_clear_playlist = QtGui.QAction(QtGui.QIcon(':/images/trashcan.png'), _("Clear Playlist").decode("utf-8"), self.main_window, shortcut="Ctrl+H",
            statusTip="Clear current playlist", triggered=self.clear_playlist_callback)
        self.context.setContextProperty('action_clear_playlist', self.action_clear_playlist)
        self.action_delete_bookmarks = QtGui.QAction(QtGui.QIcon(':/images/trashcan.png'), _("Delete All Bookmarks").decode("utf-8"), self.main_window, shortcut="Ctrl+K",
            statusTip="Delete all bookmarks", triggered=self.delete_bookmarks_callback)
        self.context.setContextProperty('action_delete_bookmarks', self.action_delete_bookmarks)
        self.action_quit = QtGui.QAction(QtGui.QIcon('/usr/share/icons/gnome/16x16/actions/exit.png'), "Quit", self.main_window, shortcut="Ctrl+Q",
            statusTip="Exit the application", triggered=self.quit_panucci)
        self.context.setContextProperty('action_quit', self.action_quit)
        # Tools menu
        self.action_playlist = QtGui.QAction(_("Playlist").decode("utf-8"), self.main_window, shortcut="Ctrl+P",
            statusTip=_("Open playlist"), triggered=self.playlist_callback)
        self.context.setContextProperty('action_playlist', self.action_playlist)
        self.action_settings = QtGui.QAction(_("Settings").decode("utf-8"), self.main_window, shortcut="Ctrl+C",
            statusTip=_("Open settings dialog"), triggered=self.settings_callback)
        self.context.setContextProperty('action_settings', self.action_settings)
        self.action_timer = QtGui.QAction(_("Sleep Timer").decode("utf-8"), self.main_window, shortcut="Ctrl+T",
            statusTip=_("Start a timed shutdown"), triggered=self.sleep_timer_callback)
        self.context.setContextProperty('action_timer', self.action_timer)
        self.shutdown_str = _("Shutdown time in minutes").decode("utf-8")
        self.context.setContextProperty('shutdown_str', self.shutdown_str)
        # Settings menu
        self.main_window_str = _("Main Window").decode("utf-8")
        self.context.setContextProperty('main_window_str', self.main_window_str)
        self.action_lock_progress = QtGui.QAction(_("Lock Progress Bar").decode("utf-8"), self.main_window, shortcut="Ctrl+L",
            statusTip="Lock progress bar", triggered=self.lock_progress_callback)
        self.action_lock_progress.setCheckable(True)
        self.action_lock_progress.setChecked(self.config.getboolean("options", "lock_progress"))
        self.context.setContextProperty('action_lock_progress', self.action_lock_progress)
        self.action_dual_action = QtGui.QAction(_("Dual Action Button").decode("utf-8"), self.main_window, shortcut="Ctrl+B",
            statusTip="Set dual action button", triggered=self.dual_action_callback)
        self.action_dual_action.setCheckable(True)
        self.action_dual_action.setChecked(self.config.getboolean("options", "dual_action_button"))
        self.context.setContextProperty('action_dual_action', self.action_dual_action)
        self.action_scrolling_labels = QtGui.QAction(_("Scrolling Labels").decode("utf-8"), self.main_window, shortcut="Ctrl+V",
            statusTip="Scroll title labels when too long", triggered=self.scrolling_labels_callback)
        self.action_scrolling_labels.setCheckable(True)
        self.action_scrolling_labels.setChecked(self.config.getboolean("options", "scrolling_labels"))
        self.context.setContextProperty('action_scrolling_labels', self.action_scrolling_labels)
        self.playback_str = _("Playback").decode("utf-8")
        self.context.setContextProperty('playback_str', self.playback_str)
        self.action_stay_at_end = QtGui.QAction(_("Stay at End").decode("utf-8"), self.main_window, shortcut="Ctrl+E",
            statusTip="Stay at file end", triggered=self.stay_at_end_callback)
        self.action_stay_at_end.setCheckable(True)
        self.action_stay_at_end.setChecked(self.config.getboolean("options", "stay_at_end"))
        self.context.setContextProperty('action_stay_at_end', self.action_stay_at_end)
        self.action_seek_back = QtGui.QAction(_("Seek Back").decode("utf-8"), self.main_window, shortcut="Ctrl+S",
            statusTip="Seek back to previous file", triggered=self.seek_back_callback)
        self.action_seek_back.setCheckable(True)
        self.action_seek_back.setChecked(self.config.getboolean("options", "seek_back"))
        self.context.setContextProperty('action_seek_back', self.action_seek_back)
        self.action_resume_all = QtGui.QAction(_("Resume All").decode("utf-8"), self.main_window, shortcut="Ctrl+R",
            statusTip="Resume all files automatically", triggered=self.resume_all_callback)
        self.action_resume_all.setCheckable(True)
        self.action_resume_all.setChecked(self.config.getboolean("options", "resume_all"))
        self.context.setContextProperty('action_resume_all', self.action_resume_all)
        self.play_mode_str = _("Play Mode").decode("utf-8")
        self.context.setContextProperty('play_mode_str', self.play_mode_str)
        self.action_play_mode_all = QtGui.QAction(_("All").decode("utf-8"), self.main_window, statusTip="Set play mode",
            triggered=self.play_mode_all_callback)
        self.action_play_mode_all.setCheckable(True)
        self.context.setContextProperty('action_play_mode_all', self.action_play_mode_all)
        self.action_play_mode_single = QtGui.QAction(_("Single").decode("utf-8"), self.main_window, statusTip="Set play mode",
            triggered=self.play_mode_single_callback)
        self.action_play_mode_single.setCheckable(True)
        self.context.setContextProperty('action_play_mode_single', self.action_play_mode_single)
        self.action_play_mode_random = QtGui.QAction(_("Random").decode("utf-8"), self.main_window, statusTip="Set play mode",
            triggered=self.play_mode_random_callback)
        self.action_play_mode_random.setCheckable(True)
        self.context.setContextProperty('action_play_mode_random', self.action_play_mode_random)
        self.action_play_mode_repeat = QtGui.QAction(_("Repeat").decode("utf-8"), self.main_window, statusTip="Set play mode",
            triggered=self.play_mode_repeat_callback)
        self.action_play_mode_repeat.setCheckable(True)
        self.context.setContextProperty('action_play_mode_repeat', self.action_play_mode_repeat)
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
        self.theme_str = _('Theme').decode("utf-8")
        self.context.setContextProperty('theme_str', self.theme_str)
        # help menu
        self.action_about = QtGui.QAction(QtGui.QIcon('about.png'), _("About").decode("utf-8"), self.main_window,
            statusTip="Show about dialog", triggered=self.about_callback)
        self.context.setContextProperty('action_about', self.action_about)
        # Player
        self.action_player_rrewind = QtGui.QAction(QtGui.QIcon(''), _("").decode("utf-8"), self.main_window,
            triggered=self.player_rrewind_callback)
        self.context.setContextProperty('action_player_rrewind', self.action_player_rrewind)
        self.action_player_rewind = QtGui.QAction(QtGui.QIcon(''), _("").decode("utf-8"), self.main_window,
            triggered=self.player_rewind_callback)
        self.context.setContextProperty('action_player_rewind', self.action_player_rewind)
        self.action_player_play = QtGui.QAction(QtGui.QIcon(''), _("").decode("utf-8"), self.main_window,
            triggered=self.player_play_callback)
        self.action_player_play.setCheckable(True)
        self.context.setContextProperty('action_player_play', self.action_player_play)
        self.action_player_forward = QtGui.QAction(QtGui.QIcon(''), _("").decode("utf-8"), self.main_window,
            triggered=self.player_forward_callback)
        self.context.setContextProperty('action_player_forward', self.action_player_forward)
        self.action_player_fforward = QtGui.QAction(QtGui.QIcon(''), _("").decode("utf-8"), self.main_window,
            triggered=self.player_fforward_callback)
        self.context.setContextProperty('action_player_fforward', self.action_player_fforward)
        self.action_player_skip_back = QtGui.QAction(QtGui.QIcon(''), _("").decode("utf-8"), self.main_window,
            triggered=self.player_skip_back_callback)
        self.context.setContextProperty('action_player_skip_back', self.action_player_skip_back)
        self.action_player_skip_forward = QtGui.QAction(QtGui.QIcon(''), _("").decode("utf-8"), self.main_window,
            triggered=self.player_skip_forward_callback)
        self.context.setContextProperty('action_player_skip_forward', self.action_player_skip_forward)
        # Playlist info
        self.info_header_str = _('Playlist item details').decode("utf-8")
        self.context.setContextProperty('info_header_str', self.info_header_str)
        self.info_title_str = _('Title:').decode("utf-8")
        self.context.setContextProperty('info_title_str', self.info_title_str)
        self.info_length_str = _('Length:').decode("utf-8")
        self.context.setContextProperty('info_length_str', self.info_length_str)
        self.info_artist_str = _('Artist:').decode("utf-8")
        self.context.setContextProperty('info_artist_str', self.info_artist_str)
        self.info_album_str = _('Album:').decode("utf-8")
        self.context.setContextProperty('info_album_str', self.info_album_str)
        self.info_filepath_str = _('Filepath:').decode("utf-8")
        self.context.setContextProperty('info_filepath_str', self.info_filepath_str)

    def make_config(self):
        self.config_qml = {}
        self.config_qml["background"] = self.config.get("options", "background")
        self.config_qml["foreground"] = self.config.get("options", "foreground")
        self.config_qml["highlight"] = self.config.get("options", "highlight")
        self.config_qml["main_width"] = self.config.getint("options", "main_width")
        self.config_qml["main_height"] = self.config.getint("options", "main_height")
        self.config_qml["button_height"] = self.config.getint("options", "button_height")
        self.config_qml["button_color"] = self.config.get("options", "button_color")
        self.config_qml["button_border_color"] = self.config.get("options", "button_border_color")
        self.config_qml["button_border_width"] = self.config.getint("options", "button_border_width")
        self.config_qml["button_radius"] = self.config.getint("options", "button_radius")
        self.config_qml["cover_height"] = self.config.getint("options", "cover_height")
        self.config_qml["progress_height"] = self.config.getint("options", "progress_height")
        self.config_qml["progress_color"] = self.config.get("options", "progress_color")
        self.config_qml["progress_bg_color"] = self.config.get("options", "progress_background_color")
        self.config_qml["font_size"] = self.config.getint("options", "font_size")
        self.config_qml["dual_delay"] = self.config.getfloat("options", "dual_action_button_delay") * 1000
        self.config_qml["scrolling"] = self.config.getboolean("options", "scrolling_labels") * 1000
        self.config_qml["button_width"] = (self.config_qml["main_width"] / 6) - 7
        self.config_qml["theme"] = self.config.get("options", "theme")
        return self.config_qml

    def quit_panucci(self):
        self.main_window.hide()
        self.playlist.quit()
        util.write_config(self.config)
        self.app.exit()

    def close_main_window_callback(self, event):
        self.quit_panucci()

    def show_main_window(self):
        self.main_window.activateWindow()

    def add_media_callback(self):
        self.view.rootObject().openFilechooser(self.get_filechooser_items(self.config.get("options", "default_folder")),
                                               self.config.get("options", "default_folder").decode('utf-8'), "add")

    @QtCore.Slot(str, str)
    def filechooser_callback(self, action, value):
        value = value.encode('utf-8')
        if action == "open":
            if os.path.isdir(os.path.expanduser(value)):
                self.config.set("options", "default_folder", value)
                self.view.rootObject().openFilechooser(self.get_filechooser_items(value), value.decode('utf-8'), False)
        elif action == "up":
            value = value.rsplit("/", 1)[0]
            self.config.set("options", "default_folder", value)
            self.view.rootObject().openFilechooser(self.get_filechooser_items(value), value.decode('utf-8'), False)
        elif action == "add":
            if os.path.exists(os.path.expanduser(value)):
                self.playlist.load(os.path.abspath(os.path.expanduser(value)))
                self.view.rootObject().openPlaylist(False, self.get_playlist_items())
        elif action == "save":
            ext = util.detect_filetype(os.path.expanduser(value))
            if not self.playlist.save_to_new_playlist(os.path.expanduser(value), ext):
                # FIX ME!
                #self.notify(_('Error saving playlist...'))
                print _('Error saving playlist...')
        elif action == "play_one":
            if os.path.exists(os.path.expanduser(value)):
                self.clear_playlist_callback()
                self.playlist.load(os.path.abspath(os.path.expanduser(value)))

    def get_filechooser_items(self, folder):
        _dir = os.path.expanduser(folder)
        dirlist = os.listdir(_dir)
        dir_list = []
        file_list = []

        for i in dirlist:
            if _dir == "/":
                _path = "/" + i
            else:
                _path = _dir + "/" + i
            if not i.startswith("."):
                if os.path.isdir(_path):
                    dir_list.append(i)
                else:
                    file_list.append(i)

        dir_list.sort(lambda x,y : cmp (x.lower(), y.lower()))
        file_list.sort(lambda x,y : cmp (x.lower(), y.lower()))
        self.filechooser_items = []
        for i in dir_list:
            self.filechooser_items.append(FilechooserItem(i, folder, True))
        for i in file_list:
            self.filechooser_items.append(FilechooserItem(i, folder, False))

        return self.filechooser_items

    def play_one_callback(self):
        self.view.rootObject().openFilechooser(self.get_filechooser_items(self.config.get("options", "default_folder")),
                                               self.config.get("options", "default_folder").decode('utf-8'), "play_one")

    def save_playlist_callback(self):
        self.view.rootObject().openFilechooser(self.get_filechooser_items(self.config.get("options", "default_folder")),
                                               self.config.get("options", "default_folder").decode('utf-8'), "save")

    def clear_playlist_callback(self):
        self.playlist.reset_playlist()

    def sleep_timer_callback(self):
        self.view.rootObject().openSleepTimer()

    @QtCore.Slot(str)
    def start_timed_shutdown(self, _minutes):
        QtCore.QTimer.singleShot(60000*int(_minutes), self.quit_panucci)

    @QtCore.Slot(str, str)
    def remove_callback(self, _id, _bid):
        self.playlist.remove_bookmark(_id, _bid)
        self.playlist_callback()

    @QtCore.Slot(str, str)
    def jump_to_callback(self, _id, _bid):
        self.playlist.load_from_bookmark_id(_id, _bid)

    def delete_bookmarks_callback(self):
        self.playlist.delete_all_bookmarks()

    def playlist_callback(self):
        self.view.rootObject().openPlaylist(True, self.get_playlist_items())

    def get_playlist_items(self):
        self.playlist_items = []
        for item, data in self.playlist.get_playlist_item_ids():
            self.playlist_items.append(PlaylistItem(item, data.get('title'), "", ""))

            for bid, bname, bpos in self.playlist.get_bookmarks_from_item_id( item ):
                self.playlist_items.append(PlaylistItem(item, bname, bid, util.convert_ns(bpos)))

        return self.playlist_items

    @QtCore.Slot(str)
    def playlist_item_info_callback(self, item_id):
        playlist_item = self.playlist.get_item_by_id(item_id)
        metadata = playlist_item.metadata
        metadata["length"] = util.convert_ns(metadata["length"])
        metadata["path"] = playlist_item.filepath.decode("utf-8")
        for i in ["title", "artist", "album"]:
            if metadata[i]:
                metadata[i] = metadata[i].decode("utf-8")
            else:
                metadata[i] = " "
        self.view.rootObject().openPlaylistItemInfo(metadata)

    def settings_callback(self):
        self.view.rootObject().openSettings()
        #from panucci.qtui.qtsettingsdialog import SettingsDialog
        #SettingsDialog(self)

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
        self.view.rootObject().start_scrolling_timer(self.config.getboolean("options", "scrolling_labels"))

    def resume_all_callback(self):
        self.set_config_option("resume_all", str(self.action_resume_all.isChecked()).lower())
        if not self.action_resume_all.isChecked():
            self.playlist.reset_all_seek_to()

    def play_mode_all_callback(self):
        self.set_config_option("play_mode", "all")

    def play_mode_single_callback(self):
        self.set_config_option("play_mode", "single")

    def play_mode_random_callback(self):
        self.set_config_option("play_mode", "random")

    def play_mode_repeat_callback(self):
        self.set_config_option("play_mode", "repeat")

    def about_callback(self):
        from panucci import about
        self.view.rootObject().openAboutDialog([about.about_name+" "+panucci.__version__, about.about_text,
                                                about.about_copyright, about.about_website])

    def set_config_option(self, option, value):
        self.config.set("options", option, value)

    def _play_file(self, filename, pause_on_load=False):
        self.playlist.load( os.path.abspath(filename) )

        if self.playlist.is_empty:
            return False

    def player_rrewind_callback(self):
        self.do_seek(-1*self.config.getint("options", "seek_long"))

    def player_rewind_callback(self):
        self.do_seek(-1*self.config.getint("options", "seek_short"))

    def player_forward_callback(self):
        self.do_seek(self.config.getint("options", "seek_short"))

    def player_fforward_callback(self):
        self.do_seek(self.config.getint("options", "seek_long"))

    def player_skip_back_callback(self):
        self.playlist.prev()

    def player_skip_forward_callback(self):
        self.playlist.next()

    def player_play_callback(self):
        self.playlist.play_pause_toggle()

    @QtCore.Slot()
    def bookmark_callback(self):
        self.playlist.add_bookmark_at_current_position()

    def do_seek(self, seek_amount):
        resp = self.playlist.do_seek(from_current=seek_amount*10**9)
        if resp:
            self.set_progress_callback( *resp )
            self.on_set_progress.emit()

    def set_progress_callback(self, time_elapsed, total_time):
        self.time_str = "%s / %s" %(util.convert_ns(time_elapsed), util.convert_ns(total_time))
        self.progress_fraction = float(time_elapsed) / float(total_time) if total_time else 0
        self.on_set_progress.emit()

    @QtCore.Slot(float)
    def on_progress_clicked(self, new_fraction):
        if not self.config.getboolean("options", "lock_progress"):
            resp = self.playlist.do_seek(percent=new_fraction)
            if resp:
                self.set_progress_callback( *resp )

    def timer_callback( self ):
        if self.playlist.playing and not self.playlist.seeking:
            pos_int, dur_int = self.playlist.get_position_duration()
            # This prevents bogus values from being set while seeking
            if pos_int >= 0 and dur_int >= 0:
                self.set_progress_callback( pos_int, dur_int )
        return True

    def get_play_pause_icon_path(self):
        if self.action_player_play.isChecked():
            _path = "media-playback-pause.png"
        else:
            _path = "media-playback-start.png"
        return _path

    def get_artist_str(self):
        if self.metadata:
            return self.metadata.get('artist', 0).decode('utf-8')
        else:
            return ""

    def get_album_str(self):
        if self.metadata:
            return self.metadata.get('album', 0).decode('utf-8')
        else:
            return ""

    def get_title_str(self):
        if self.metadata:
            return self.metadata.get('title', 0).decode('utf-8')
        else:
            return ""

    def set_text_x(self):
        if self.metadata:
            self.view.rootObject().set_text_x()

    def get_cover_str(self):
        if self.metadata and self.metadata.has_key('image') and self.metadata['image']:
            return "image://cover/" + os.urandom(10)
        else:
            return ""

    def get_time_str(self):
        return self.time_str

    def get_progress(self):
        return self.progress_fraction

    on_play_pause = QtCore.Signal()
    on_set_progress = QtCore.Signal()
    on_set_metadata = QtCore.Signal()
    play_pause_icon_path = QtCore.Property(str, get_play_pause_icon_path, notify=on_play_pause)
    time_string = QtCore.Property(str, get_time_str, notify=on_set_progress)
    progress = QtCore.Property(float, get_progress, notify=on_set_progress)
    artist_string = QtCore.Property(str, get_artist_str, notify=on_set_metadata)
    album_string = QtCore.Property(str, get_album_str, notify=on_set_metadata)
    title_string = QtCore.Property(str, get_title_str, notify=on_set_metadata)
    cover_string = QtCore.Property(str, get_cover_str, notify=on_set_metadata)

    def on_player_stopped(self):
        self.timer.stop()
        self.action_player_play.setChecked(False)
        self.on_play_pause.emit()
        if self.metadata:
            estimated_length = self.metadata.get('length', 0)
            self.set_progress_callback( 0, estimated_length )
        #self.set_controls_sensitivity(False)

    def on_player_playing(self):
        self.timer_callback()
        self.timer.start()
        self.action_player_play.setChecked(True)
        self.on_play_pause.emit()
        #self.set_controls_sensitivity(True)

    def on_player_paused( self, position, duration ):
        self.timer.stop()
        self.action_player_play.setChecked(False)
        self.on_play_pause.emit()
        #self.set_progress_callback( position, duration )

    def on_player_new_track(self):
        self.time_str = "00:00 / 00:00"
        self.progress_fraction = 0
        self.metadata = None
        self.on_set_progress.emit()
        self.on_set_metadata.emit()
        self.main_window.setWindowTitle("Panucci")

    def on_player_new_metadata(self):
        self.metadata = self.playlist.get_file_metadata()
        position = self.playlist.get_current_position()
        estimated_length = self.metadata.get('length', 0)
        self.set_progress_callback(position, estimated_length)
        self.on_set_progress.emit()
        self.on_set_metadata.emit()
        self.set_text_x()
        _title = self.metadata["title"]
        if len(_title) > 25:
            _title = _title[:24] + '...'
        self.main_window.setWindowTitle(_title.decode('utf-8'))

    def on_player_end_of_playlist(self, loop):
        if not loop:
            estimated_length = self.metadata.get('length', 0)
            self.set_progress_callback( 0, estimated_length )

    def on_player_reset_playlist(self):
        self.on_player_stopped()
        self.on_player_new_track()

    @QtCore.Slot(str)
    def open_external_url(self, url):
        os.system("xdg-open " + url)

class ImageProvider(QtDeclarative.QDeclarativeImageProvider):
    def __init__(self, main):
        QtDeclarative.QDeclarativeImageProvider.__init__(self, QtDeclarative.QDeclarativeImageProvider.Pixmap)
        self.__main = main

    def requestPixmap(self, id, size, requestedSize):
        size = requestedSize.width()
        pixmap = QtGui.QPixmap()
        pixmap.loadFromData(self.__main.metadata['image'])
        pixmap = pixmap.scaled(size, size, mode=QtCore.Qt.SmoothTransformation)
        return pixmap

class PlaylistItem(QtCore.QObject):
    def __init__(self, _id, _caption, _bookmark, _position):
        QtCore.QObject.__init__(self)
        if isinstance(_caption, str):
            _caption = _caption.decode('utf-8')
        self._caption = _caption
        self._id = _id
        self._bookmark = _bookmark
        self._position = _position

    changed = QtCore.Signal()

    def _get_id(self):
        return self._id
    
    def _get_caption(self):
        return self._caption

    def _get_bookmark(self):
        return self._bookmark

    def _get_position(self):
        return self._position

    item_id = QtCore.Property(str, _get_id, notify=changed)
    caption = QtCore.Property(unicode, _get_caption, notify=changed)
    bookmark_id = QtCore.Property(str, _get_bookmark, notify=changed)
    position = QtCore.Property(str, _get_position, notify=changed)

class FilechooserItem(QtCore.QObject):
    def __init__(self, _caption, _path, _directory):
        QtCore.QObject.__init__(self)
        if isinstance(_caption, str):
            _caption = _caption.decode('utf-8')
        if isinstance(_path, str):
            _path = _path.decode('utf-8')

        self._caption = _caption
        self._path = _path
        self._directory = _directory

    changed = QtCore.Signal()

    def _get_caption(self):
        return self._caption

    def _get_path(self):
        return self._path

    def _get_directory(self):
        return self._directory

    caption = QtCore.Property(unicode, _get_caption, notify=changed)
    path = QtCore.Property(unicode, _get_path, notify=changed)
    directory = QtCore.Property(bool, _get_directory, notify=changed)

class ThemeController(QtCore.QObject):
    def __init__(self, config):
        QtCore.QObject.__init__(self)

        self.config = config
        self.config_theme = ConfigParser.SafeConfigParser()
        #_file = open(util.find_data_file("theme-all.conf"))
        #self.config.readfp(_file)
        #_file.close()
        _file = open(panucci.THEME_FILE)
        self.config_theme.readfp(_file)
        _file.close()

    @QtCore.Slot(str)
    def set_theme(self, theme):
        self.config.set("options", "theme", theme.strip().lower())
        self.changed.emit()

    def _get_background(self):
        return "#" + self.config_theme.get(self.config.get("options", "theme"), "background")

    def _get_foreground(self):
        return "#" + self.config_theme.get(self.config.get("options", "theme"), "foreground")

    def _get_highlight(self):
        return "#" + self.config_theme.get(self.config.get("options", "theme"), "highlight")

    def _get_button_color(self):
        return "#" + self.config_theme.get(self.config.get("options", "theme"), "button_color")

    def _get_button_border_color(self):
        return "#" + self.config_theme.get(self.config.get("options", "theme"), "button_border_color")

    def _get_progress_color(self):
        return "#" + self.config_theme.get(self.config.get("options", "theme"), "progress_color")

    def _get_progress_bg_color(self):
        return "#" + self.config_theme.get(self.config.get("options", "theme"), "progress_background_color")

    changed = QtCore.Signal()
    background = QtCore.Property(str, _get_background, notify=changed)
    foreground = QtCore.Property(str, _get_foreground, notify=changed)
    highlight = QtCore.Property(str, _get_highlight, notify=changed)
    button_color = QtCore.Property(str, _get_button_color, notify=changed)
    button_border_color = QtCore.Property(str, _get_button_border_color, notify=changed)
    progress_color = QtCore.Property(str, _get_progress_color, notify=changed)
    progress_bg_color = QtCore.Property(str, _get_progress_bg_color, notify=changed)
