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
import sys
import os
import time
import cgi
import dbus

from PySide  import QtCore
from PySide import QtGui

from panucci import platform
from panucci import util

##################################################
# PlaylistTab
##################################################
class PlaylistTab():
    def __init__(self, main, player):
        self.__log = logging.getLogger('panucci.panucci.BookmarksWindow')
        #self.player.playlist.register( 'file_queued', lambda x,y,z: self.update_model() )
        #self.player.playlist.register( 'bookmark_added', self.on_bookmark_added )
        self.__gui_root = main
        self.player = player
        self.main_window = QtGui.QMainWindow(main.main_window)
        self.main_window.setWindowTitle(_("Playlist"))
        widget = QtGui.QWidget()
        layout = QtGui.QVBoxLayout()
        widget.setLayout(layout)
        self.main_window.setCentralWidget(widget)
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)

        self.tw = QtGui.QTreeView()
        layout.addWidget(self.tw, 3)

        hlayout = QtGui.QHBoxLayout()
        layout.addLayout(hlayout)

        self.button_file = QtGui.QPushButton(QtGui.QIcon(util.find_data_file('')), _("Add File"))
        self.button_file.clicked.connect(self.button_file_callback)
        #self.button_rrewind.setFixedHeight(settings.config.getint("options", "button_height"))
        self.button_dir = QtGui.QPushButton(QtGui.QIcon(util.find_data_file('')), _("Add Folder"))
        self.button_dir.clicked.connect(self.button_dir_callback)
        #self.button_dir.setFixedHeight(settings.config.getint("options", "button_height"))
        self.button_remove = QtGui.QPushButton(QtGui.QIcon(util.find_data_file('')), _("Remove"))
        self.button_remove.clicked.connect(self.button_remove_callback)
        #self.button_remove.setFixedHeight(settings.config.getint("options", "button_height"))
        self.button_jump = QtGui.QPushButton(QtGui.QIcon(util.find_data_file('')), _("Jump to"))
        self.button_jump.clicked.connect(self.button_jump_callback)
        #self.button_jump.setFixedHeight(settings.config.getint("options", "button_height"))
        self.button_info = QtGui.QPushButton(QtGui.QIcon(util.find_data_file('')), _("Info"))
        self.button_info.clicked.connect(self.button_info_callback)
        #self.button_info.setFixedHeight(settings.config.getint("options", "button_height"))
        self.button_clear = QtGui.QPushButton(QtGui.QIcon(util.find_data_file('')), _("Clear"))
        self.button_clear.clicked.connect(self.button_clear_callback)
        #self.button_clear.setFixedHeight(settings.config.getint("options", "button_height"))

        hlayout.addWidget(self.button_file)
        hlayout.addWidget(self.button_dir)
        hlayout.addWidget(self.button_remove)
        hlayout.addWidget(self.button_jump)
        hlayout.addWidget(self.button_info)
        hlayout.addWidget(self.button_clear)


    def button_file_callback(self):
        pass

    def button_dir_callback(self):
        pass

    def button_remove_callback(self):
        pass

    def button_jump_callback(self):
        pass

    def button_info_callback(self):
        pass

    def button_clear_callback(self):
        pass
