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

from __future__ import absolute_import

import gtk
import gobject
import pango

from panucci import platform

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

    LEFT, NO_CHANGE, RIGHT = [ -1, 0, 1 ]

    def __init__( self, pango_markup, update_interval=100, pixel_jump=1,
                  delay_btwn_scrolls=0, delay_halfway=0 ):
        """ Creates a new ScrollingLabel widget.

              pixel_jump: the amount of pixels the text moves in one update
              pango_markup: the markup that is displayed
              update_interval: the amount of time (in milliseconds) between
                scrolling updates
              delay_btwn_scrolls: The amount of time (in milliseconds) to
                wait after a scroll has completed and the next one begins
              delay_halfway: The amount of time (in milliseconds) to wait
                when the text reaches the far right.

            Scrolling is controlled by the 'scrolling' property, it must be
            set to True for the text to start moving. Updating of the pango
            markup is supported by setting the 'markup' property.

            Note: the properties can be read from to get their current status
        """

        gtk.DrawingArea.__init__(self)
        self.__x_offset = 0
        self.__x_direction = self.LEFT
        self.__x_alignment = 0
        self.__y_alignment = 0.5
        self.__scrolling_timer_id = None
        self.__scrolling_possible = False
        self.__scrolling = False

        if platform.FREMANTLE:
            self._fg = gtk.gdk.color_parse('#fff')
        else:
            l = gtk.Label()
            s = l.get_style()
            self._fg = s.text[gtk.STATE_NORMAL]

        # user-defined parameters (can be changed on-the-fly)
        self.update_interval = update_interval
        self.delay_btwn_scrolls = delay_btwn_scrolls
        self.delay_halfway = delay_halfway
        self.pixel_jump = pixel_jump

        self.__graphics_context = None
        self.__pango_layout = self.create_pango_layout('')
        self.markup = pango_markup

        self.connect('expose-event', self.__on_expose_event)
        self.connect('size-allocate', lambda w,a: self.__reset_widget() )
        self.connect('map', lambda w: self.__reset_widget() )

    def __set_scrolling(self, value):
        if value:
            self.__start_scrolling()
        else:
            self.__stop_scrolling()

    def set_markup(self, markup):
        """ Set the pango markup to be displayed by the widget """
        self.__pango_layout.set_markup(markup)
        self.__reset_widget()

    def get_markup( self ):
        """ Returns the current markup contained in the widget """
        return self.__pango_layout.get_text()

    def set_alignment(self, x, y):
        """ Set the text's alignment on the x axis when it's not possible to
            scroll. The y axis setting does nothing atm. """

        for i in x,y:
            assert isinstance( i, (float, int) ) and 0 <= i <= 1

        self.__x_alignment = x
        self.__y_alignment = y

    def get_alignment( self ):
        """ Returns the current alignment settings (x, y). """
        return self.__x_alignment, self.__y_alignment

    scrolling = property( lambda s: s.__scrolling, __set_scrolling )
    markup    = property( get_markup, set_markup )
    alignment = property( get_alignment, lambda s,i: s.set_alignment(*i) )

    def __on_expose_event( self, widget, event ):
        """ Draws the text on the widget. This should be called indirectly by
            using self.queue_draw() """

        if self.__graphics_context is None:
            self.__graphics_context = self.window.new_gc()

        self.window.draw_layout(self.__graphics_context,
                                int(self.__x_offset), 0, self.__pango_layout,
                                self._fg)

    def __reset_widget( self ):
        """ Reset the offset and find out whether or not it's even possible
            to scroll the current text. Useful for when the window gets resized
            or when new markup is set. """

        # if there's no window, we can ignore this reset request because
        # when the window is created this will be called again.
        if self.window is None:
            return

        win_x, win_y = self.window.get_size()
        lbl_x, lbl_y = self.__pango_layout.get_pixel_size()

        # If we don't request the proper height, the label might get squashed
        # down to 0px. (this could still happen on the horizontal axis but we
        # aren't affected by this problem in Panucci *yet*)
        self.set_size_request( -1, lbl_y )

        self.__scrolling_possible = lbl_x > win_x

        # Remove any lingering scrolling timers
        self.__scrolling_timer = None

        if self.__scrolling:
            self.__start_scrolling()

        if self.__scrolling_possible:
            self.__x_offset = 0
        else:
            self.__x_offset = (win_x - lbl_x) * self.__x_alignment

        self.queue_draw()

    def __scroll_once(self, halfway_callback=None, finished_callback=None):
        """ Moves the text by 'self.pixel_jump' every time this is called.
            Returns False when the text has completed one scrolling period and
            'finished_callback' is run.
            Returns False halfway through (when the text is all the way to the
            right) if 'halfway_callback' is set after running the callback.
        """

        # prevent an accidental scroll (there's a race-condition somewhere
        # but I'm too lazy to find out where).
        if not self.__scrolling_possible:
            return False

        rtn = True
        win_x, win_y = self.window.get_size()
        lbl_x, lbl_y = self.__pango_layout.get_pixel_size()

        self.__x_offset += self.pixel_jump * self.__x_direction

        if self.__x_direction == self.LEFT and self.__x_offset < win_x - lbl_x:
            self.__x_direction = self.RIGHT
            # set the offset to the maximum left bound otherwise some
            # characters might get chopped off if using large pixel_jump's
            self.__x_offset = win_x - lbl_x

            if halfway_callback is not None:
                halfway_callback()
                rtn = False

        elif self.__x_direction == self.RIGHT and self.__x_offset > 0:
            # end of scroll period; reset direction
            self.__x_direction = self.LEFT
            # don't allow the offset to be greater than 0
            self.__x_offset = 0
            if finished_callback is not None:
                finished_callback()

            # return False because at this point we've completed one scroll
            # period; this kills off any timers running this function
            rtn = False

        self.queue_draw()
        return rtn

    def __scroll_wait_callback(self, delay):
        # Waits 'delay', then calls the scroll function
        self.__scrolling_timer = gobject.timeout_add( delay, self.__scroll )

    def __scroll(self):
        """ When called, scrolls the text back and forth indefinitely while
            waiting self.delay_btwn_scrolls between each scroll period. """

        if self.__scrolling_possible:
            self.__scrolling_timer = gobject.timeout_add(
                self.update_interval, self.__scroll_once,
                lambda: self.__scroll_wait_callback(self.delay_halfway),
                lambda: self.__scroll_wait_callback(self.delay_btwn_scrolls) )
        else:
            self.__scrolling_timer = None

    def __scrolling_timer_get(self):
        return self.__scrolling_timer_id

    def __scrolling_timer_set(self, val):
        """ When changing the scrolling timer id, make sure that only one
            timer is running at a time. This removes the previous timer
            before adding a new one. """

        if self.__scrolling_timer_id is not None:
            gobject.source_remove( self.__scrolling_timer_id )
            self.__scrolling_timer_id = None

        self.__scrolling_timer_id = val

    __scrolling_timer = property( __scrolling_timer_get, __scrolling_timer_set )

    def __start_scrolling(self):
        """ Make the text start scrolling """
        self.__scrolling = True
        if self.__scrolling_timer is None and self.__scrolling_possible:
            self.__scroll()

    def __stop_scrolling(self):
        """ Make the text stop scrolling """
        self.__scrolling = False
        self.__scrolling_timer = None


if __name__ == '__main__':
    w = gtk.Window()
    w.set_geometry_hints(w, 100, 20)
    hb = gtk.HBox(homogeneous=True, spacing=1)
    w.add(hb)

    # scroll 7 pixels per 0.2 seconds, wait halfway for 0.5 seconds and finally
    # wait 2 seconds after a complete scroll. wash, rinse, repeat.
    l = ScrollingLabel('N/A', 100, 1, 2000, 500)
    l.markup = 'some random text 1234'
    hb.pack_end(l)

    btn = gtk.Button('start/stop')
    hb.pack_start(btn)
    btn.connect('clicked', lambda w,e: setattr(e,'scrolling', not e.scrolling), l)

    w.connect('destroy', gtk.main_quit)
    w.show_all()
    gtk.main()

