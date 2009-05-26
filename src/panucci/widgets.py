#
# -*- coding: utf-8 -*-
#
# Additional GTK Widgets for use in Panucci
# Copyright (c) 2009 Thomas Perl <thpinfo.com>
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

import gtk
import gobject
import pango

class DualActionButton(gtk.Button):
    """
    This button allows the user to carry out two different actions,
    depending on how long the button is pressed. In order for this
    to work, you need to specify two widgets that will be displayed
    inside this DualActionButton and two callbacks (actions) that
    will be called from the UI thread when the button is released
    and a valid action is detected.

    You normally create such a button like this:

    def action_a():
        ...
    def action_b():
        ...

    DURATION = 1.0  # in seconds
    b = DualActionButton(gtk.Label('Default Action'), action_a,
                         gtk.Label('Longpress Action'), action_b,
                         duration=DURATION)
    window.add(b)
    """
    (DEFAULT, LONGPRESS) = range(2)

    def __init__(self, default_widget, default_action,
                       longpress_widget=None, longpress_action=None,
                       duration=0.5, longpress_enabled=True):
        gtk.Button.__init__(self)

        default_widget.show()
        if longpress_widget is not None:
            longpress_widget.show()

        if longpress_widget is None or longpress_action is None:
            longpress_enabled = False

        self.__default_widget = default_widget
        self.__longpress_widget = longpress_widget
        self.__default_action = default_action
        self.__longpress_action = longpress_action
        self.__duration = duration
        self.__current_state = -1
        self.__timeout_id = None
        self.__pressed_state = False
        self.__inside = False
        self.__longpress_enabled = longpress_enabled

        self.connect('pressed', self.__pressed)
        self.connect('released', self.__released)
        self.connect('enter', self.__enter)
        self.connect('leave', self.__leave)
        self.connect_after('expose-event', self.__expose_event)

        self.set_state(self.DEFAULT)

    def set_longpress_enabled(self, longpress_enabled):
        self.__longpress_enabled = longpress_enabled

    def get_longpress_enabled(self):
        return self.__longpress_enabled

    def set_duration(self, duration):
        self.__duration = duration

    def get_duration(self):
        return self.__duration

    def set_state(self, state):
        if state != self.__current_state:
            if not self.__longpress_enabled and state == self.LONGPRESS:
                return False
            self.__current_state = state
            child = self.get_child()
            if child is not None:
                self.remove(child)
            if state == self.DEFAULT:
                self.add(self.__default_widget)
            elif state == self.LONGPRESS:
                self.add(self.__longpress_widget)
            else:
                raise ValueError('State has to be either DEFAULT or LONGPRESS.')

        return False

    def get_state(self):
        return self.__current_state

    def add_timeout(self):
        self.remove_timeout()
        self.__timeout_id = gobject.timeout_add(int(1000*self.__duration),
                self.set_state, self.LONGPRESS)

    def remove_timeout(self):
        if self.__timeout_id is not None:
            gobject.source_remove(self.__timeout_id)
            self.__timeout_id = None

    def __pressed(self, widget):
        self.__pressed_state = True
        self.add_timeout()
        self.__force_redraw()

    def __released(self, widget):
        self.__pressed_state = False
        self.remove_timeout()
        state = self.get_state()
        self.__force_redraw()

        if self.__inside:
            if state == self.DEFAULT:
                self.__default_action()
            elif state == self.LONGPRESS:
                self.__longpress_action()

        self.set_state(self.DEFAULT)

    def __enter(self, widget):
        self.__inside = True
        self.__force_redraw()
        if self.__pressed_state:
            self.add_timeout()

    def __leave(self, widget):
        self.__inside = False
        self.__force_redraw()
        if self.__pressed_state:
            self.set_state(self.DEFAULT)
            self.remove_timeout()

    def __force_redraw(self):
        self.window.invalidate_rect(self.__get_draw_rect(True), False)

    def __get_draw_rect(self, for_invalidation=False):
        rect = self.get_allocation()
        width, height, BORDER = 10, 5, 6
        brx, bry = (rect.x+rect.width-BORDER-width,
                    rect.y+rect.height-BORDER-height)

        displacement_x = self.style_get_property('child_displacement-x')
        displacement_y = self.style_get_property('child_displacement-y')

        if for_invalidation:
            # For redraw (rect invalidate), update both the "normal"
            # and the "pressed" area by simply adding the displacement
            # to the size (to remove the "other" drawing, too
            return gtk.gdk.Rectangle(brx, bry, width+displacement_x,
                    height+displacement_y)
        else:
            if self.__pressed_state and self.__inside:
                brx += displacement_x
                bry += displacement_y
            return gtk.gdk.Rectangle(brx, bry, width, height)

    def __expose_event(self, widget, event):
        style = self.get_style()
        rect = self.__get_draw_rect()
        if self.__longpress_enabled:
            style.paint_handle(self.window, gtk.STATE_NORMAL, gtk.SHADOW_NONE,
                    rect, self, 'Detail', rect.x, rect.y, rect.width,
                    rect.height, gtk.ORIENTATION_HORIZONTAL)


class ScrollingLabel(gtk.DrawingArea):
    """ A simple scrolling label widget - if the text doesn't fit in the
        container, it will scroll back and forth at a pre-determined interval.
    """

    def __init__(self, pango_markup, update_interval=100, pixel_jump=1):
        """ Creates a new ScrollingLabel widget.
              pango_markup: the markup that is displayed
              update_interval: the amount of time (in milliseconds) between
                scrolling updates
              pixel_jump: the amount of pixels the text moves in one update
        """

        gtk.DrawingArea.__init__(self)
        self.__x_offset = 0
        self.__x_direction = -1 # left=-1, right=1
        self.__scrolling_timer = None
        self.update_interval = update_interval
        self.pixel_jump = pixel_jump

        self.__graphics_context = None
        self.__pango_layout = self.create_pango_layout('')
        self.set_markup( pango_markup )
        
        self.connect('expose-event', self.__on_expose_event)
        self.connect('size-allocate', self.__on_size_allocate_event)

    def __on_expose_event( self, widget, event ):
        if self.__graphics_context is None:
            self.__graphics_context = self.window.new_gc()
        
        self.window.draw_layout( self.__graphics_context,
                                 self.__x_offset, 0, self.__pango_layout )
    
    def __on_size_allocate_event( self, widget, allocation ):
        # if the window is resized, we reset the offset otherwise the text
        # might get stuck at a no longer valid offset.
        self.__x_offset = 0
    
    def set_markup( self, pango_markup ):
        """ Set the displayed markup """
        self.__pango_layout.set_markup(pango_markup)
    
    def __scroll(self):
        """ Moves the text by 'pixel_jump' in the proper direction """
        win_x, win_y = self.window.get_size()
        lbl_x, lbl_y = self.__pango_layout.get_pixel_size()
        
        # in this case the text is smaller than the container, so don't scroll
        if win_x - lbl_x >= 0:
            return True
        
        # the offset will only be negative, at 0 the first letter is visible
        # at the containter width minus the text length (a negative number)
        # the last letter will be visible.
        if self.__x_offset > 0 or self.__x_offset < win_x - lbl_x:
            self.__x_direction = -1 if self.__x_direction == 1 else 1
        
        self.__x_offset += self.pixel_jump * self.__x_direction
        self.queue_draw()
        
        return True # we must return True to keep the timer running
    
    def start_scrolling(self):
        """ Make the text start scrolling """
        if self.__scrolling_timer is None:
            self.__scrolling_timer = gobject.timeout_add( self.update_interval,
                                                          self.__scroll )
    
    def stop_scrolling(self):
        """ Make the text stop scrolling """
        if self.__scrolling_timer is not None:
            gobject.source_remove( self.__scrolling_timer )
            self.__scrolling_timer = None

    def __set_scrolling( self, scrolling ):
        if scrolling:
            self.start_scrolling()
        else:
            self.stop_scrolling()

    # allow querying/setting whether or not the text is scrolling
    scrolling = property( lambda : __scrolling_timer != None, __set_scrolling )

