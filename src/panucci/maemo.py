# -*- coding: utf-8 -*-
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

import gobject
import osso

import panucci


class MaemoDevice(object):
    def __init__(self):
        self._osso_context = osso.Context('Panucci', panucci.__version__, False)
        self._osso_device_state = osso.DeviceState(self._osso_context)
        self.anti_blank_timer_id = None

    def disable_blanking(self):
        """Inhibit blanking of the screen

        Calling this function will keep the backlight turned on.
        """
        self.anti_blank_timer_id is not None:
            self.anti_blank_timer_id = gobject.timeout_add(1000*59, \
                    self._blanking_timer_callback)

    def enable_blanking(self):
        """(Re-)enable blanking of the screen

        If blanking has been inhibited previously, this will
        allow blanking the screen again.
        """
        if self.anti_blank_timer_id is not None:
            gobject.source_remove(self.anti_blank_timer_id)

    def _blanking_timer_callback(self):
        self._osso_device_state.display_blanking_pause()
        return True

