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
from PySide  import QtCore
from PySide import QtGui

from panucci import about
from panucci import platform
from panucci import util

class AboutDialog:
    def __init__(self, parent, version):
        self.ad = QtGui.QDialog(parent)
        self.ad.setWindowTitle(_("About"))
        main_layout = QtGui.QVBoxLayout()
        self.ad.setLayout(main_layout)

        hlayout = QtGui.QHBoxLayout()
        label = QtGui.QLabel()
        pixmap = QtGui.QPixmap(util.find_data_file('panucci_64x64.png'))
        label.setPixmap(pixmap)
        hlayout.addWidget(label)

        vlayout = QtGui.QVBoxLayout()
        label = QtGui.QLabel()
        label.setText('<b><big>' + about.about_name + " " + version + '</b></big>')
        vlayout.addWidget(label, 2)
        label = QtGui.QLabel()
        label.setText(about.about_text)
        vlayout.addWidget(label, 2)
        label = QtGui.QLabel(about.about_copyright)
        vlayout.addWidget(label, 2)
        label = QtGui.QLabel("<qt><a href='%s'>"%(about.about_website) + about.about_website + "</a></qt>")
        label.setOpenExternalLinks(True)
        vlayout.addWidget(label, 2)
        hlayout.addLayout(vlayout, 2)
        main_layout.addLayout(hlayout)

        layout = QtGui.QHBoxLayout()
        label = QtGui.QLabel()
        layout.addWidget(label, 2)
        button = QtGui.QPushButton(_("Credits"))
        button.clicked.connect(self.show_credits)
        layout.addWidget(button)
        button = QtGui.QPushButton(_("Close"))
        button.clicked.connect(self.close)
        layout.addWidget(button)
        main_layout.addLayout(layout)

        self.cd = QtGui.QDialog(self.ad)
        self.cd.setWindowTitle(_("Credits"))
        self.cd.setModal(True)
        layout = QtGui.QVBoxLayout()
        self.cd.setLayout(layout)

        tw = QtGui.QTabWidget()
        layout.addWidget(tw)
        te = QtGui.QTextEdit()
        tw.addTab(te, _("Authors"))
        te.setReadOnly(True)
        for i in about.about_authors:
            te.append(i)

        hlayout = QtGui.QHBoxLayout()
        label = QtGui.QLabel()
        hlayout.addWidget(label, 2)
        button = QtGui.QPushButton(_("Close"))
        button.clicked.connect(self.close_credits)
        hlayout.addWidget(button)

        layout.addLayout(hlayout)
        self.ad.exec_()

    def close(self):
        self.ad.close()

    def show_credits(self):
        self.cd.show()

    def close_credits(self):
        self.cd.close()
