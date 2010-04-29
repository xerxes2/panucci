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

import os.path

# Variables that can be used to query platform status
MAEMO = False
FREMANTLE = False
DESKTOP = True


def file_contains(filename, content):
    try:
        for line in open(filename):
            if content in line:
                return True
    except:
        return False


def detect():
    """Detect current environment

    This should be called once from the launcher.
    """
    global MAEMO
    global FREMANTLE
    global DESKTOP

    if os.path.exists('/etc/osso_software_version') or \
            os.path.exists('/proc/component_version') or \
            file_contains('/etc/issue/', 'maemo'):
        MAEMO = True
        DESKTOP = False

        # Check for Maemo 5 (fremantle)
        if file_contains('/etc/issue', 'Maemo 5'):
            MAEMO = True
            FREMANTLE = True
            DESKTOP = False

