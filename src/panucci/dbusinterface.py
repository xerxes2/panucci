#!/usr/bin/env python

import logging
import dbus
import dbus.service

class panucciInterface(dbus.service.Object):
    """ Panucci's d-bus interface """

    def __init__(self, player, bus_name, path='/panucciInterface'):
        self.__log = logging.getLogger('panucci.dbusinterface.panucciInterface')
        dbus.service.Object.__init__( self, object_path=path, bus_name=bus_name )
        self.player = player

    @dbus.service.method('org.panucci.panucciInterface')
    def play(self):
        self.player.play()

    @dbus.service.method('org.panucci.panucciInterface')
    def pause(self):
        self.player.pause()

    @dbus.service.method('org.panucci.panucciInterface')
    def stop(self):
        self.player.stop()


init_dbus = lambda player: panucciInterface( player,
    dbus.service.BusName('org.panucci.panucciInterface', dbus.SessionBus()) )
