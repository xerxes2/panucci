#
# -*- coding: utf-8 -*-
#
# Additional GTK Widgets for use in Panucci
# Copyright (c) 2009 Thomas Perl <thpinfo.com>
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

import gtk
import gobject

class DualActionButton(gtk.Button):
    """
    This button allows the user to carry out two different actions,
    depending on how long the button is pressed. In order for this
    to work, you need to specify two widgets that will be displayed
    inside this DualActionButton and two callbacks (actions) that
    will be called from the UI thread when the button is released
    and a valid action is detected.

    You normally create such a button like this:

    def action_a():
        ...
    def action_b():
        ...

    DURATION = 1.0  # in seconds
    b = DualActionButton(gtk.Label('Default Action'), action_a,
                         gtk.Label('Longpress Action'), action_b,
                         duration=DURATION)
    window.add(b)
    """
    (DEFAULT, LONGPRESS) = range(2)

    def __init__(self, default_widget, default_action,
                       longpress_widget=None, longpress_action=None,
                       duration=0.5, longpress_enabled=True):
        gtk.Button.__init__(self)

        default_widget.show()
        if longpress_widget is not None:
            longpress_widget.show()

        if longpress_widget is None or longpress_action is None:
            longpress_enabled = False

        self.__default_widget = default_widget
        self.__longpress_widget = longpress_widget
        self.__default_action = default_action
        self.__longpress_action = longpress_action
        self.__duration = duration
        self.__current_state = -1
        self.__timeout_id = None
        self.__pressed_state = False
        self.__inside = False
        self.__longpress_enabled = longpress_enabled

        self.connect('pressed', self.__pressed)
        self.connect('released', self.__released)
        self.connect('enter', self.__enter)
        self.connect('leave', self.__leave)

        self.set_state(self.DEFAULT)

    def set_longpress_enabled(self, longpress_enabled):
        self.__longpress_enabled = longpress_enabled

    def get_longpress_enabled(self):
        return self.__longpress_enabled

    def set_duration(self, duration):
        self.__duration = duration

    def get_duration(self):
        return self.__duration

    def set_state(self, state):
        if state != self.__current_state:
            if not self.__longpress_enabled and state == self.LONGPRESS:
                return False
            self.__current_state = state
            child = self.get_child()
            if child is not None:
                self.remove(child)
            if state == self.DEFAULT:
                self.add(self.__default_widget)
            elif state == self.LONGPRESS:
                self.add(self.__longpress_widget)
            else:
                raise ValueError('State has to be either DEFAULT or LONGPRESS.')

        return False

    def get_state(self):
        return self.__current_state

    def add_timeout(self):
        self.remove_timeout()
        self.__timeout_id = gobject.timeout_add(int(1000*self.__duration),
                self.set_state, self.LONGPRESS)

    def remove_timeout(self):
        if self.__timeout_id is not None:
            gobject.source_remove(self.__timeout_id)
            self.__timeout_id = None

    def __pressed(self, widget):
        self.__pressed_state = True
        self.add_timeout()

    def __released(self, widget):
        self.__pressed_state = False
        self.remove_timeout()
        state = self.get_state()

        if self.__inside:
            if state == self.DEFAULT:
                self.__default_action()
            elif state == self.LONGPRESS:
                self.__longpress_action()

        self.set_state(self.DEFAULT)

    def __enter(self, widget):
        self.__inside = True
        if self.__pressed_state:
            self.add_timeout()

    def __leave(self, widget):
        self.__inside = False
        if self.__pressed_state:
            self.set_state(self.DEFAULT)
            self.remove_timeout()

