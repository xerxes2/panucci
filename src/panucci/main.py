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
#
# Based on http://thpinfo.com/2008/panucci/:
#  A resuming media player for Podcasts and Audiobooks
#  Copyright (c) 2008-05-26 Thomas Perl <thpinfo.com>
#  (based on http://pygstdocs.berlios.de/pygst-tutorial/seeking.html)

from __future__ import absolute_import

import dbus
import dbus.glib
import logging
import logging.handlers
import os.path
from sys import excepthook

import panucci
from panucci.settings import settings
# Detect the platform we're running on
from panucci import platform
platform.detect()

def run(opts, args):
    if args:
        filepath = args[0]
        if not '://' in filepath:
            filepath = os.path.abspath(filepath)
    elif opts.queue_filename:
        filepath = os.path.abspath(opts.queue_filename)
    else:
        filepath = None

    # Attempt to contact an already-running copy of Panucci
    session_bus = dbus.SessionBus()
    try:
        if session_bus.name_has_owner('org.panucci.panucciInterface'):
            remote_object = session_bus.get_object(
                'org.panucci.panucciInterface', '/panucciInterface' )
            print 'Found panucci instance already running, will try to use it...'
        else:
            remote_object = None
    except dbus.exceptions.DBusException:
        remote_object = None

    if remote_object is None:
        # configure logging
        init_logging( logging.DEBUG if opts.debug else logging.ERROR )

        if opts.qt:
            from panucci.qtui.qtmain import PanucciGUI
        elif opts.qml:
            from panucci.qmlui.qmlmain import PanucciGUI
        elif opts.gtk:
            from panucci.gtkui.gtkmain import PanucciGUI
        elif settings.config.get("options", "gui") == "qt":
            from panucci.qtui.qtmain import PanucciGUI
        elif settings.config.get("options", "gui") == "qml":
            from panucci.qmlui.qmlmain import PanucciGUI
        else:
            from panucci.gtkui.gtkmain import PanucciGUI
        PanucciGUI(settings, filepath)
    else:
        if filepath is not None:
            if opts.queue_filename is not None:
                remote_object.queue_file( filepath )
            else:
                remote_object.play_file( filepath )

        remote_object.show_main_window()

def init_logging( log_level ):
    """ Configure the logging module for panucci """
    logger = logging.getLogger('panucci')
    logger.setLevel( logging.DEBUG )

    # the stream handler (logging to the console)
    sh = logging.StreamHandler()
    sh.setLevel( log_level )
    fmt = logging.Formatter('%(levelname)s:%(name)s %(message)s')
    sh.setFormatter(fmt)
    logger.addHandler(sh)

    # the file handler (logging to a file)
    fh = logging.handlers.RotatingFileHandler(panucci.LOGFILE, \
            backupCount=0, maxBytes=25*1024)

    fh.doRollover() # reset the logfile at startup
    fh.setLevel( logging.DEBUG ) # log everything to the file
    fmt = logging.Formatter('%(asctime)s %(levelname)s:%(name)s %(message)s')
    fh.setFormatter(fmt)
    logger.addHandler(fh)

    # force all exceptions to pass through the logger
    excepthook = lambda *args: logger.critical( 'Exception caught:',
                                                    exc_info=args )
