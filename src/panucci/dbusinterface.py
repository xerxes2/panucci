#!/usr/bin/env python
#
# This file is part of Panucci.
# Copyright (c) 2008-2009 The Panucci Audiobook and Podcast Player Project
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

import logging
import dbus
import dbus.service

import util

class panucciInterface(dbus.service.Object):
    """ Panucci's d-bus interface """

    def __init__(self, bus_name, path='/panucciInterface'):
        self.__log = logging.getLogger('panucci.dbusinterface.panucciInterface')
        dbus.service.Object.__init__(self, object_path=path, bus_name=bus_name)

        self.player = None
        self.gui = None
        self.headset_device = None

        if util.platform == util.MAEMO:
            headset_button = dbus.SystemBus().get_object(
                'org.freedesktop.Hal', '/org/freedesktop/Hal/devices/'
                'platform_retu_headset_logicaldev_input' )
            self.headset_device = dbus.Interface(
                headset_button, 'org.freedesktop.Hal.Device')

    def register_player(self, player):
        self.__log.debug('Registered player.')
        self.player = player

    def register_gui(self, gui):
        self.__log.debug('Registered GUI.')
        self.gui = gui

    @dbus.service.method('org.panucci.panucciInterface')
    def play(self):
        self.__log.debug('play() called')
        if self.player is not None: self.player.play()

    @dbus.service.method('org.panucci.panucciInterface')
    def pause(self):
        self.__log.debug('pause() called')
        if self.player is not None: self.player.pause()

    @dbus.service.method('org.panucci.panucciInterface')
    def stop(self):
        self.__log.debug('stop() called')
        if self.player is not None: self.player.stop()

    @dbus.service.method('org.panucci.panucciInterface')
    def playPause(self):
        self.__log.debug('playPause() called')
        if self.player is not None: self.player.play_pause_toggle()

    @dbus.service.method('org.panucci.panucciInterface', in_signature='s')
    def play_file(self, filepath):
        self.__log.debug('play_file() called')
        if self.player is not None: self.player.play_file(filepath)

    @dbus.service.method('org.panucci.panucciInterface', in_signature='s')
    def queue_file(self, filepath):
        self.__log.debug('queue_file() called')
        if self.player is not None: self.player.playlist.append(filepath)

    @dbus.service.method('org.panucci.panucciInterface', in_signature='su')
    def insert_file(self, pos, filepath):
        self.__log.debug('insert_file() called')
        if self.player is not None: self.player.playlist.insert(pos, filepath)

    @dbus.service.method('org.panucci.panucciInterface', in_signature='sb')
    def load_directory(self, directory, append):
        self.__log.debug('load_directory() called')
        if self.player is not None: self.player.playlist.load_directory(
            directory, append )

    @dbus.service.method('org.panucci.panucciInterface')
    def show_main_window(self):
        self.__log.debug('show_main_window() called')
        if self.gui is not None: self.gui.show_main_window()

interface = panucciInterface(
    dbus.service.BusName('org.panucci.panucciInterface', dbus.SessionBus()) )

