#!/usr/bin/env python

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
        if self.player is not None: self.player.play()

    @dbus.service.method('org.panucci.panucciInterface')
    def pause(self):
        if self.player is not None: self.player.pause()

    @dbus.service.method('org.panucci.panucciInterface')
    def stop(self):
        if self.player is not None: self.player.stop()

    @dbus.service.method('org.panucci.panucciInterface')
    def playPause(self):
        if self.player is not None: self.player.play_pause_toggle()

    @dbus.service.method('org.panucci.panucciInterface', in_signature='s')
    def play_file(self, filepath):
        if self.player is not None: self.player.play_file(filepath)

    @dbus.service.method('org.panucci.panucciInterface', in_signature='s')
    def queue_file(self, filepath):
        if self.player is not None: self.player.playlist.append(filepath)

    @dbus.service.method('org.panucci.panucciInterface', in_signature='su')
    def insert_file(self, pos, filepath):
        if self.player is not None: self.player.playlist.insert(pos, filepath)

    @dbus.service.method('org.panucci.panucciInterface')
    def show_main_window(self):
        if self.gui is not None: self.gui.show_main_window()

interface = panucciInterface(
    dbus.service.BusName('org.panucci.panucciInterface', dbus.SessionBus()) )

