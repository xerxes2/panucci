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
import logging

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
        self.create_actions()
        engine = self.context.engine()
        ip = ImageProvider(self)
        engine.addImageProvider("cover", ip)
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

    def make_config(self):
        self.config_qml = {}
        self.config_qml["background"] = self.config.get("options", "background")
        self.config_qml["foreground"] = self.config.get("options", "foreground")
        self.config_qml["main_width"] = self.config.getint("options", "main_width")
        self.config_qml["main_height"] = self.config.getint("options", "main_height")
        self.config_qml["button_height"] = self.config.getint("options", "button_height")
        self.config_qml["button_color"] = self.config.get("options", "button_color")
        self.config_qml["button_border_color"] = self.config.get("options", "button_border_color")
        self.config_qml["button_border_width"] = self.config.getint("options", "button_border_width")
        self.config_qml["cover_height"] = self.config.getint("options", "cover_height")
        self.config_qml["progress_height"] = self.config.getint("options", "progress_height")
        self.config_qml["progress_color"] = self.config.get("options", "progress_color")
        self.config_qml["progress_bg_color"] = self.config.get("options", "progress_background_color")
        self.config_qml["font_size"] = self.config.getint("options", "font_size")
        self.config_qml["dual_delay"] = self.config.getfloat("options", "dual_action_button_delay") * 1000
        self.config_qml["scrolling"] = self.config.getboolean("options", "scrolling_labels") * 1000
        bwidth = (self.config_qml["main_width"] / 6) - 7
        self.config_qml["button_width"] = (self.config_qml["main_width"] / 6) - 7
        return self.config_qml

    def quit_panucci(self):
        self.main_window.hide()
        self.playlist.quit()
        util.write_config(self.config)
        self.app.exit()

    def create_actions(self):
        # File menu
        self.action_add_file = QtGui.QAction(QtGui.QIcon(':/actions/add.png'), _("Add File").decode("utf-8"), self.main_window, shortcut="Ctrl+A",
            statusTip="Add file to playlist", triggered=self.add_file_callback)
        self.action_add_folder = QtGui.QAction(QtGui.QIcon(':/images/open.png'), _("Add Folder").decode("utf-8"), self.main_window, shortcut="Ctrl+D",
            statusTip="Add folder to playlist", triggered=self.add_folder_callback)
        self.action_play_one = QtGui.QAction(QtGui.QIcon(''), _("Play One").decode("utf-8"), self.main_window, shortcut="Ctrl+O",
            statusTip="Play one file", triggered=self.play_one_callback)
        self.action_save_playlist = QtGui.QAction(QtGui.QIcon(':/images/save.png'), _("Save Playlist").decode("utf-8"), self.main_window, shortcut="Ctrl+W",
            statusTip="Save current playlist as m3u", triggered=self.save_playlist_callback)
        self.action_clear_playlist = QtGui.QAction(QtGui.QIcon(':/images/trashcan.png'), _("Clear Playlist").decode("utf-8"), self.main_window, shortcut="Ctrl+H",
            statusTip="Clear current playlist", triggered=self.clear_playlist_callback)
        self.action_delete_bookmarks = QtGui.QAction(QtGui.QIcon(':/images/trashcan.png'), _("Delete All Bookmarks").decode("utf-8"), self.main_window, shortcut="Ctrl+K",
            statusTip="Delete all bookmarks", triggered=self.delete_bookmarks_callback)
        self.action_quit = QtGui.QAction(QtGui.QIcon('/usr/share/icons/gnome/16x16/actions/exit.png'), "Quit", self.main_window, shortcut="Ctrl+Q",
            statusTip="Exit the application", triggered=self.quit_panucci)
        self.context.setContextProperty('action_quit', self.action_quit)
        # Tools menu
        self.action_playlist = QtGui.QAction(_("Playlist"), self.main_window, shortcut="Ctrl+P",
            statusTip=_("Open playlist"), triggered=self.playlist_callback)
        self.action_settings = QtGui.QAction(_("Settings"), self.main_window, shortcut="Ctrl+C",
            statusTip=_("Open settings dialog"), triggered=self.settings_callback)
        self.action_timer = QtGui.QAction(_("Sleep Timer"), self.main_window, shortcut="Ctrl+T",
            statusTip=_("Start a timed shutdown"), triggered=self.create_timer_dialog)
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
        self.action_resume_all = QtGui.QAction(_("Resume All").decode("utf-8"), self.main_window, shortcut="Ctrl+R",
            statusTip="Resume all files automatically", triggered=self.resume_all_callback)
        self.action_resume_all.setCheckable(True)
        self.action_resume_all.setChecked(self.config.getboolean("options", "resume_all"))
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

    def create_menus(self):
        # Player menu
        self.menu_player = self.main_window.menuBar().addMenu("Player")
        self.menu_player.addAction(self.action_settings)
        self.menu_player.addAction(self.action_playlist)
        self.menu_player.addAction(self.action_add_file)
        self.menu_player.addAction(self.action_add_folder)
        self.menu_player.addAction(self.action_play_one)
        self.menu_player.addAction(self.action_clear_playlist)
        self.menu_player.addAction(self.action_timer)
        self.menu_player.addAction(self.action_about)
        # Playlist menu
        self.menu_playlist = self.__playlist_tab.main_window.menuBar().addMenu("Playlist")
        self.menu_playlist.addAction(self.action_save_playlist)
        self.menu_playlist.addAction(self.action_delete_bookmarks)
 
    def create_timer_dialog(self):
        response = QtGui.QInputDialog.getInteger(self.main_window, _("Sleep Timer"), _("Shutdown time in minutes"),
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

    def play_one_callback(self):
        filenames = qtutil.get_file_from_filechooser(self)
        if filenames:
            self.clear_playlist_callback()
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
            self.__playlist_tab.update_model()

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
        from panucci.qtui import qtaboutdialog
        qtaboutdialog.AboutDialog(self.main_window, panucci.__version__)

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

    def do_seek(self, seek_amount):
        resp = self.playlist.do_seek(from_current=seek_amount*10**9)
        if resp:
            self.set_progress_callback( *resp )
            self.on_set_progress.emit()

    def set_progress_callback(self, time_elapsed, total_time):
        """ times must be in nanoseconds """
        self.time_str = "%s / %s" %(util.convert_ns(time_elapsed), util.convert_ns(total_time))
        #self.progress.setFormat( time_string )
        self.progress_fraction = float(time_elapsed) / float(total_time) if total_time else 0
        #self.progress.setValue( int(fraction*100) )

    @QtCore.Slot(float)
    def on_progress_clicked(self, new_fraction):
        if not self.config.getboolean("options", "lock_progress"):
            resp = self.playlist.do_seek(percent=new_fraction)
            if resp:
                self.set_progress_callback( *resp )
                self.on_set_progress.emit()

    def timer_callback( self ):
        if self.playlist.playing and not self.playlist.seeking:
            pos_int, dur_int = self.playlist.get_position_duration()
            # This prevents bogus values from being set while seeking
            if pos_int >= 0 and dur_int >= 0:
                self.set_progress_callback( pos_int, dur_int )
            self.on_set_progress.emit()
        return True

    def get_play_pause_icon_path(self):
        if self.action_player_play.isChecked():
            _path = "media-playback-pause.png"
        else:
            _path = "media-playback-start.png"
        return _path

    def get_artist_str(self):
        if self.metadata:
            return self.metadata.get('artist', 0)
        else:
            return ""

    def get_album_str(self):
        if self.metadata:
            return self.metadata.get('album', 0)
        else:
            return ""

    def get_title_str(self):
        if self.metadata:
            return self.metadata.get('title', 0)
        else:
            return ""

    def set_text_x(self):
        if self.metadata:
            self.view.rootObject().set_text_x()

    def get_cover_str(self):
        if self.metadata and self.metadata.has_key('image') and self.metadata['image']:
            return "image://cover"
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
            self.on_set_progress.emit()
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
        #self.label_cover.hide()
        self.on_set_progress.emit()
        self.on_set_metadata.emit()
        self.main_window.setWindowTitle("Panucci")

    def on_player_new_metadata(self):
        self.metadata = self.playlist.get_file_metadata()
        #self.set_metadata(self.metadata)
        position = self.playlist.get_current_position()
        estimated_length = self.metadata.get('length', 0)
        self.set_progress_callback(position, estimated_length)
        self.on_set_progress.emit()
        self.on_set_metadata.emit()
        self.set_text_x()
        _title = self.metadata["title"]
        if len(_title) > 25:
            _title = _title[:24] + '...'
        self.main_window.setWindowTitle(_title)

    def on_player_end_of_playlist(self, loop):
        if not loop:
            estimated_length = self.metadata.get('length', 0)
            self.set_progress_callback( 0, estimated_length )

    def on_player_reset_playlist(self):
        self.on_player_stopped()
        self.on_player_new_track()
        self.reset_progress()
        self.main_window.setWindowTitle("Panucci")

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
