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

import os.path

# Variables that can be used to query platform status
MAEMO = False
FREMANTLE = False
HARMATTAN = False
MEEGO = False
SAILFISH = False
HANDSET = False
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
    global HARMATTAN
    global MEEGO
    global SAILFISH
    global HANDSET
    global DESKTOP

    if os.path.exists('/etc/os-release'):
        if file_contains('/etc/os-release', 'sailfishos'):
            SAILFISH = True
            HANDSET = True
            DESKTOP = False

    elif os.path.exists('/etc/osso_software_version') or \
            os.path.exists('/proc/component_version') or \
            file_contains('/etc/issue', 'maemo') or \
            file_contains('/etc/issue', 'Harmattan') or \
            os.path.exists('/etc/meego-release'):
        HANDSET = True
        DESKTOP = False

        if os.path.exists('/etc/osso_software_version') or \
                os.path.exists('/proc/component_version') or \
                file_contains('/etc/issue', 'maemo') or \
                file_contains('/etc/issue', 'Harmattan'):
            MAEMO = True

            if file_contains('/etc/issue', 'Maemo 5'):
                FREMANTLE = True
            elif file_contains('/etc/issue', 'Harmattan'):
                HARMATTAN = True

        elif os.path.exists('/etc/meego-release'):
            MEEGO = True
