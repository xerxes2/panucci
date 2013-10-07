# -*- coding: utf-8 -*-
#
# gPodder - A media aggregator and podcast client
# Copyright (c) 2005-2010 Thomas Perl and the gPodder Team
#
# gPodder is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# gPodder is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

from gi.repository import Gtk as gtk
import dbus
from panucci import platform
from panucci import about

_ = lambda x: x

class AboutDialog:
    def __init__(self, parent, version):
        ad = gtk.AboutDialog()
        ad.set_transient_for(parent)
        ad.set_name(about.about_name)
        ad.set_version(version)
        ad.set_copyright(about.about_copyright)
        ad.set_comments(about.about_text)
        ad.set_website(about.about_website)
        ad.set_authors(about.about_authors)
        ad.set_translator_credits(_('translator-credits'))
        ad.set_logo_icon_name(about.about_icon_name)
        ad.run()
        ad.destroy()
