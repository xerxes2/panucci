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

from PySide  import QtCore
from PySide import QtGui

from panucci import platform

class SettingsDialog:
    def __init__(self, main):
        self.main = main
        self.dialog = QtGui.QDialog(self.main.main_window)
        self.dialog.setWindowTitle(_("Settings"))
        main_layout = QtGui.QVBoxLayout()
        self.dialog.setLayout(main_layout)

        label = QtGui.QLabel("Main Window")
        main_layout.addWidget(label)
        # It does not seem to be possible to use action as proxies.
        self.box_scrolling_labels = QtGui.QCheckBox(_("Scrolling Labels"))
        self.box_scrolling_labels.setChecked(self.main.action_scrolling_labels.isChecked())
        self.box_scrolling_labels.stateChanged.connect(self.scrolling_labels_callback)
        main_layout.addWidget(self.box_scrolling_labels)

        self.box_lock_progress = QtGui.QCheckBox(_("Lock Progress Bar"))
        self.box_lock_progress.setChecked(self.main.action_lock_progress.isChecked())
        self.box_lock_progress.stateChanged.connect(self.lock_progress_callback)
        main_layout.addWidget(self.box_lock_progress)

        self.box_dual_action = QtGui.QCheckBox(_("Dual Action Button"))
        self.box_dual_action.setChecked(self.main.action_dual_action.isChecked())
        self.box_dual_action.stateChanged.connect(self.dual_action_callback)
        main_layout.addWidget(self.box_dual_action)

        label = QtGui.QLabel("Playback")
        main_layout.addWidget(label)

        self.box_stay_at_end = QtGui.QCheckBox(_("Stay at End"))
        self.box_stay_at_end.setChecked(self.main.action_stay_at_end.isChecked())
        self.box_stay_at_end.stateChanged.connect(self.stay_at_end_callback)
        main_layout.addWidget(self.box_stay_at_end)

        self.box_seek_back = QtGui.QCheckBox(_("Seek Back"))
        self.box_seek_back.setChecked(self.main.action_seek_back.isChecked())
        self.box_seek_back.stateChanged.connect(self.seek_back_callback)
        main_layout.addWidget(self.box_seek_back)

        label = QtGui.QLabel("Play Mode")
        main_layout.addWidget(label)
        group_play_mode = QtGui.QButtonGroup()

        self.radio_play_mode_all = QtGui.QRadioButton(_("All"))
        self.radio_play_mode_all.setChecked(self.main.action_play_mode_all.isChecked())
        self.radio_play_mode_all.toggled.connect(self.play_mode_all_callback)
        group_play_mode.addButton(self.radio_play_mode_all)
        main_layout.addWidget(self.radio_play_mode_all)

        self.radio_play_mode_single = QtGui.QRadioButton(_("Single"))
        self.radio_play_mode_single.setChecked(self.main.action_play_mode_single.isChecked())
        self.radio_play_mode_single.toggled.connect(self.play_mode_single_callback)
        group_play_mode.addButton(self.radio_play_mode_single)
        main_layout.addWidget(self.radio_play_mode_single)

        self.radio_play_mode_random = QtGui.QRadioButton(_("Random"))
        self.radio_play_mode_random.setChecked(self.main.action_play_mode_random.isChecked())
        self.radio_play_mode_random.toggled.connect(self.play_mode_random_callback)
        group_play_mode.addButton(self.radio_play_mode_random)
        main_layout.addWidget(self.radio_play_mode_random)

        self.radio_play_mode_repeat = QtGui.QRadioButton(_("Repeat"))
        self.radio_play_mode_repeat.setChecked(self.main.action_play_mode_repeat.isChecked())
        self.radio_play_mode_repeat.toggled.connect(self.play_mode_repeat_callback)
        group_play_mode.addButton(self.radio_play_mode_repeat)
        main_layout.addWidget(self.radio_play_mode_repeat)

        layout = QtGui.QHBoxLayout()
        layout.addStretch(2)
        button = QtGui.QPushButton(_("Close"))
        button.clicked.connect(self.close)
        layout.addWidget(button)
        main_layout.addLayout(layout)

        self.dialog.exec_()

    def close(self):
        self.dialog.close()

    def scrolling_labels_callback(self):
        self.main.action_scrolling_labels.setChecked(self.box_scrolling_labels.isChecked())

    def lock_progress_callback(self):
        self.main.action_lock_progress.setChecked(self.box_lock_progress.isChecked())

    def dual_action_callback(self):
        self.main.action_dual_action.setChecked(self.box_dual_action.isChecked())

    def stay_at_end_callback(self):
        self.main.action_stay_at_end.setChecked(self.box_stay_at_end.isChecked())

    def seek_back_callback(self):
        self.main.action_seek_back.setChecked(self.box_seek_back.isChecked())

    def play_mode_all_callback(self):
        self.main.action_play_mode_all.setChecked(self.radio_play_mode_all.isChecked())

    def play_mode_single_callback(self):
        self.main.action_play_mode_single.setChecked(self.radio_play_mode_single.isChecked())

    def play_mode_random_callback(self):
        self.main.action_play_mode_random.setChecked(self.radio_play_mode_random.isChecked())

    def play_mode_repeat_callback(self):
        self.main.action_play_mode_repeat.setChecked(self.radio_play_mode_repeat.isChecked())
