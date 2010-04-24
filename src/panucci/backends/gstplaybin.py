#!/usr/bin/env python
#
# This file is part of Panucci.
# Copyright (c) 2008-2010 The Panucci Audiobook and Podcast Player Project
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

from __future__ import absolute_import

import gst
import logging

from panucci.backends import gstbase

class GstPlaybinPlayer(gstbase.GstBasePlayer):
    """  """
    
    def __init__(self):
        gstbase.GstBasePlayer.__init__(self)
        self.__log = logging.getLogger('panucci.backends.GstPlaybinPlayer')
        self.__log.debug("Initialized GstPlaybinPlayer backend")
    
    def _setup_player(self, filetype=None):
        self.__log.debug("Creating playbin-based gstreamer player")
        self._player = gst.element_factory_make('playbin2', 'player')
        self._filesrc = self._player
        self._filesrc_property = 'uri'
        self._volume_control = self._player
        self._volume_multiplier = 1.
        self._volume_property = 'volume'
        return True

