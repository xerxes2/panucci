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

class DualActionButton(QtGui.QPushButton):
    def __init__(self, config, default_icon, default_action, longpress_icon=None, longpress_action=None):
        super(DualActionButton, self).__init__()

        self.config = config
        self.default_icon = default_icon
        self.default_action = default_action
        if longpress_icon:
            self.longpress = True
            self.longpress_icon = longpress_icon
            self.longpress_action = longpress_action
        else:
            self.longpress = False

        self.setIcon(default_icon)
        self.state = False
        self.timer = QtCore.QTimer()
        self.timer.setInterval(int(1000*self.config.getfloat("options", "dual_action_button_delay")))
        self.timer.timeout.connect(self.timer_callback)

        self.pressed.connect(self.pressed_callback)
        self.released.connect(self.released_callback)

    def timer_callback(self):
        self.timer.stop()
        self.state = True
        self.setIcon(self.longpress_icon)

    def pressed_callback(self):
        if self.longpress and self.config.getboolean("options", "dual_action_button"):
            self.timer.start()

    def released_callback(self):
        self.timer.stop()
        if self.state and self.longpress:
            self.longpress_action()
        else:
            self.default_action()
        self.state = False
        self.setIcon(self.default_icon)

class ScrollingLabel(QtGui.QGraphicsView):
    def __init__(self, config):
        super(ScrollingLabel, self).__init__()

        self.config = config
        self.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.setFrameStyle(QtGui.QFrame.NoFrame)

        self.scene = QtGui.QGraphicsScene()
        self.setScene(self.scene)
        self.scene.setBackgroundBrush(self.palette().window())

        self.text_item = self.scene.addText("")
        color = QtGui.QColor("#" + self.config.get("options", "scrolling_color"))
        self.text_item.setDefaultTextColor(color)
        self.height = self.text_item.boundingRect().height() + 10
        self.setFixedHeight(self.height)

        self.timer = QtCore.QTimer()
        self.timer.setInterval(100)
        self.timer.timeout.connect(self.timer_callback)

        self.scroll_left = True
        self.set_scrolling(self.config.getboolean("options", "scrolling_labels"))
        self.scene_width = self.scene.width()
        self.text_width = self.text_item.boundingRect().width()

    def setText(self, text):
        self.text_item.setHtml(text)
        self.text_width = self.text_item.boundingRect().width()
        if self.alignment() == QtCore.Qt.AlignLeft:
            self.text_item.setX(0)
        else:
            _x = (self.scene_width - self.text_width) / 2.0
            self.text_item.setX(_x)

        self.text_item.update()
        self.scene.update()
        self.viewport().update()

    def resizeEvent(self, event):
        if event:
            self.scene.setSceneRect(0, 0, self.width(), self.height)
        self.scene_width = self.scene.width()
        if not self.scrolling:
            if self.alignment() == QtCore.Qt.AlignHCenter:
                _x = (self.scene_width - self.text_width) / 2.0
                self.text_item.setX(_x)
            else:
                self.text_item.setX(0)
        elif self.scene_width > self.text_width:
            if self.alignment() == QtCore.Qt.AlignHCenter:
                _x = (self.scene_width - self.text_width) / 2.0
                self.text_item.setX(_x)
            else:
                self.text_item.setX(0)

    def set_scrolling(self, scrolling):
        self.scrolling = scrolling
        if scrolling:
            self.timer.start()
        else:
            self.timer.stop()
            self.scroll_left = True
            self.resizeEvent(False)

    def timer_callback(self):
        if self.text_width > self.scene_width:
            if self.scroll_left:
                if self.text_item.x() > (self.scene_width - self.text_width):
                    self.text_item.setX(self.text_item.x() - 1.0)
                else:
                    self.scroll_left = False
            else:
                if self.text_item.x() < 0:
                    self.text_item.setX(self.text_item.x() + 1.0)
                else:
                    self.scroll_left = True
