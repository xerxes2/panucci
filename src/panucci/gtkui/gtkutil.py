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

import gtk
import gobject
import os.path

from panucci import platform
from panucci import util

try:
    import hildon
except:
    pass

coverart_sizes = {
    'normal'            : 110,
    'maemo'             : 200,
    'maemo fullscreen'  : 275,
}

def generate_image(filename, is_stock=False):
    image = None
    if is_stock:
        image = gtk.image_new_from_stock(
            filename, gtk.icon_size_from_name('panucci-button') )
    else:
        filename = util.find_data_file(filename)
        if filename is not None:
            image = gtk.image_new_from_file(filename)
    if image is not None:
        if platform.MAEMO:
            image.set_padding(20, 20)
        else:
            image.set_padding(5, 5)
        image.show()
    return image

def image(widget, filename, is_stock=False):
    child = widget.get_child()
    if child is not None:
        widget.remove(child)
    image = generate_image(filename, is_stock)
    if image is not None:
        widget.add(image)

def dialog( toplevel_window, title, question, description,
            affirmative_button=gtk.STOCK_YES, negative_button=gtk.STOCK_NO,
            abortion_button=gtk.STOCK_CANCEL ):

    """Present the user with a yes/no/cancel dialog.
    The return value is either True, False or None, depending on which
    button has been pressed in the dialog:

        affirmative button (default: Yes)    => True
        negative button    (defaut: No)      => False
        abortion button    (default: Cancel) => None

    When the dialog is closed with the "X" button in the window manager
    decoration, the return value is always None (same as abortion button).

    You can set any of the affirmative_button, negative_button or
    abortion_button values to "None" to hide the corresponding action.
    """
    dlg = gtk.MessageDialog( toplevel_window, gtk.DIALOG_MODAL,
                             gtk.MESSAGE_QUESTION, message_format=question )

    dlg.set_title(title)

    if abortion_button is not None:
        dlg.add_button(abortion_button, gtk.RESPONSE_CANCEL)
    if negative_button is not None:
        dlg.add_button(negative_button, gtk.RESPONSE_NO)
    if affirmative_button is not None:
        dlg.add_button(affirmative_button, gtk.RESPONSE_YES)

    dlg.format_secondary_text(description)

    response = dlg.run()
    dlg.destroy()

    if response == gtk.RESPONSE_YES:
        return True
    elif response == gtk.RESPONSE_NO:
        return False
    elif response in [gtk.RESPONSE_CANCEL, gtk.RESPONSE_DELETE_EVENT]:
        return None

def get_file_from_filechooser(main, folder=False, save_file=False, save_to=None):

    if folder:
        open_action = gtk.FILE_CHOOSER_ACTION_SELECT_FOLDER
    else:
        open_action = gtk.FILE_CHOOSER_ACTION_OPEN

    if platform.FREMANTLE:
        if save_file:
            dlg = gobject.new(hildon.FileChooserDialog, \
                    action=gtk.FILE_CHOOSER_ACTION_SAVE)
        else:
            dlg = gobject.new(hildon.FileChooserDialog, \
                    action=open_action)
    elif platform.MAEMO:
        if save_file:
            args = ( main.main_window, gtk.FILE_CHOOSER_ACTION_SAVE )
        else:
            args = ( main.main_window, open_action )

        dlg = hildon.FileChooserDialog( *args )
    else:
        if save_file:
            args = ( _('Select file to save playlist to'), None,
                gtk.FILE_CHOOSER_ACTION_SAVE,
                (( gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT,
                gtk.STOCK_SAVE, gtk.RESPONSE_OK )) )
        else:
            args = ( _('Select podcast or audiobook'), None, open_action,
                (( gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT,
                gtk.STOCK_OPEN, gtk.RESPONSE_OK )) )

        dlg = gtk.FileChooserDialog(*args)

    current_folder = os.path.expanduser(main.config.get("options", "default_folder"))

    if current_folder is not None and os.path.isdir(current_folder):
        dlg.set_current_folder(current_folder)

    if save_file and save_to is not None:
        dlg.set_current_name(save_to)

    if dlg.run() == gtk.RESPONSE_OK:
        filename = dlg.get_filename()
        main.config.set("options", "default_folder", dlg.get_current_folder())
    else:
        filename = None

    dlg.destroy()
    return filename

def set_stock_button_text( button, text ):
    alignment = button.get_child()
    hbox = alignment.get_child()
    image, label = hbox.get_children()
    label.set_text(text)
